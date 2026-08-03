"""
Coding Challenge Endpoints
Handle challenge generation, retrieval, and code evaluation.
"""

import os
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body, Depends
from app.services.coding_engine import CodingEngine
from app.models.coding import CodingResponse, CodingChallenge, CodeSubmission, EvaluationResult
from app.utils.file_handler import FileStorage as FileHandler

router = APIRouter()


def _resolve_file(filename: str) -> str:
    """Safely resolve and validate a filename to a full path."""
    if os.path.basename(filename) != filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    upload_dir = FileHandler.get_upload_dir()
    file_path = os.path.join(upload_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Session file not found. Please upload your resume again.")
    return file_path


@router.post("/generate-challenge", response_model=CodingResponse)
async def generate_challenge_endpoint(
    filename: str = Body(..., embed=True, description="Unique filename from upload response"),
    force_regenerate: bool = Body(False, embed=True, description="Force regeneration even if cached")
):
    """
    Generate an original, domain-relevant coding challenge based on the candidate's profile.
    The challenge is tailored to the candidate's skill domain and experience level.
    Includes starter code in Python, JavaScript, Java, and C++.
    """
    file_path = _resolve_file(filename)

    # Validate profile exists
    profile_path = f"{file_path}.json"
    if not os.path.exists(profile_path):
        raise HTTPException(
            status_code=422,
            detail="Resume analysis not found. Please analyze your resume before starting the coding challenge."
        )

    # Check cache
    challenge_path = f"{file_path}.coding.json"
    if not force_regenerate and os.path.exists(challenge_path):
        try:
            with open(challenge_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    challenges = [CodingChallenge(**ch) for ch in data]
                else:
                    # Handle old single challenge format
                    challenges = [CodingChallenge(**data)]
                return CodingResponse(
                    success=True,
                    challenge_id=filename,
                    challenges=challenges,
                    message="Challenges loaded from cache"
                )
        except Exception:
            pass  # Cache corrupted — regenerate

    # Generate fresh challenges
    challenges = await CodingEngine.generate_for_session(file_path, force_regenerate=force_regenerate)

    if not challenges:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate coding challenges. The AI may be temporarily unavailable. Please try again."
        )

    return CodingResponse(
        success=True,
        challenge_id=filename,
        challenges=challenges,
        message=f"Generated {len(challenges)} coding challenges (Easy, Medium, Hard)"
    )


@router.post("/submit-code", response_model=EvaluationResult)
async def submit_code_endpoint(
    submission: CodeSubmission
):
    """
    Evaluate submitted code against the challenge test cases.
    Provides per-test-case results, complexity analysis, and detailed feedback.
    Supports Python, JavaScript, Java, and C++.
    """
    filename = submission.challenge_id
    if not filename:
        raise HTTPException(status_code=400, detail="challenge_id (filename) is required")

    if not submission.code or not submission.code.strip():
        raise HTTPException(status_code=400, detail="No code was submitted. Please write your solution first.")

    # Validate language
    supported_languages = {"python", "javascript", "java", "cpp"}
    language = submission.language.lower().strip()
    if language not in supported_languages:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{submission.language}'. Supported: {', '.join(sorted(supported_languages))}"
        )

    file_path = _resolve_file(filename)

    # Load challenge
    challenge_path = f"{file_path}.coding.json"
    if not os.path.exists(challenge_path):
        raise HTTPException(
            status_code=404,
            detail="Challenge not found. Please generate a challenge before submitting code."
        )

    try:
        with open(challenge_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                if submission.challenge_index < 0 or submission.challenge_index >= len(data):
                    raise HTTPException(status_code=400, detail="Invalid challenge index")
                challenge = CodingChallenge(**data[submission.challenge_index])
            else:
                challenge = CodingChallenge(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load challenge: {e}")

    # EVALUATE CODE IMMEDIATELY
    evaluation_result = await CodingEngine.evaluate_code(challenge, submission.code, language, skipped=submission.skipped)
    
    # Save submission and evaluation results to file
    submission_path = f"{file_path}.coding_submission.json"
    submissions = {}
    if os.path.exists(submission_path):
        try:
            with open(submission_path, "r", encoding="utf-8") as f:
                submissions = json.load(f)
        except: pass
    
    submissions[str(submission.challenge_index)] = {
        "code": submission.code,
        "language": language,
        "skipped": submission.skipped,
        "timestamp": datetime.utcnow().isoformat(),
        "evaluation": {
            "success": evaluation_result.success,
            "score": evaluation_result.score,
            "attempted": evaluation_result.attempted,
            "passed_test_cases": evaluation_result.passed_test_cases,
            "total_test_cases": evaluation_result.total_test_cases,
            "feedback": evaluation_result.feedback
        }
    }
    
    try:
        with open(submission_path, "w", encoding="utf-8") as f:
            json.dump(submissions, f)
    except Exception as e:
        print(f"Failed to save coding submission: {e}")

    return evaluation_result
