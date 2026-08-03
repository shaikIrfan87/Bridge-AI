"""
Quiz Endpoints
Handle quiz generation, retrieval, and AI-powered evaluation.
"""

import os
import json
from fastapi import APIRouter, HTTPException, Body, Depends
from app.services.quiz_generator import QuizGenerator
from app.models.quiz import QuizResponse, Quiz, QuizSubmission, QuizEvaluationResponse
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


@router.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz_endpoint(
    filename: str = Body(..., embed=True, description="Unique filename from upload response"),
    force_regenerate: bool = Body(False, embed=True, description="Force regeneration even if cached")
):
    """
    Generate a personalized quiz based on the candidate's full profile.
    Uses resume data including work experience and projects for industry-relevant questions.
    """
    file_path = _resolve_file(filename)

    # Check profile exists
    profile_path = f"{file_path}.json"
    if not os.path.exists(profile_path):
        raise HTTPException(
            status_code=422,
            detail="Resume analysis not found. Please analyze your resume first before generating a quiz."
        )

    # Check cache (unless force_regenerate)
    quiz_path = f"{file_path}.quiz.json"
    if not force_regenerate and os.path.exists(quiz_path):
        try:
            with open(quiz_path, "r", encoding="utf-8") as f:
                quiz_data = json.load(f)
                quiz = Quiz(**quiz_data)
                return QuizResponse(
                    success=True,
                    quiz_id=filename,
                    quiz=quiz,
                    message=f"Quiz loaded from cache ({quiz.total_questions} questions)"
                )
        except Exception:
            pass  # Cache corrupted — regenerate

    # Generate fresh quiz
    quiz = await QuizGenerator.generate_for_session(file_path, force_regenerate=force_regenerate)

    if not quiz:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate quiz. The AI may be temporarily unavailable. Please try again."
        )

    return QuizResponse(
        success=True,
        quiz_id=filename,
        quiz=quiz,
        message=f"Quiz generated successfully with {quiz.total_questions} personalized questions"
    )


@router.post("/evaluate-quiz", response_model=QuizEvaluationResponse)
async def evaluate_quiz_endpoint(
    submission: QuizSubmission
):
    """
    Submit quiz answers for AI-powered scoring.
    Returns detailed per-question scores, matched/missing keywords, and overall feedback.
    """
    filename = submission.quiz_id
    if not filename:
        raise HTTPException(status_code=400, detail="quiz_id (filename) is required")

    file_path = _resolve_file(filename)

    # Load cached quiz
    quiz_path = f"{file_path}.quiz.json"
    if not os.path.exists(quiz_path):
        raise HTTPException(
            status_code=404,
            detail="Quiz not found. Please generate a quiz before submitting answers."
        )

    try:
        with open(quiz_path, "r", encoding="utf-8") as f:
            quiz_data = json.load(f)
            quiz = Quiz(**quiz_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load quiz: {e}")

    # Load profile to get experience level
    experience_level = "Mid-Level"
    profile_path = f"{file_path}.json"
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
                experience_level = profile_data.get("experience_level", "Mid-Level")
        except Exception:
            pass

    # Save RAW Submission to File (Deferring Evaluation for Speed)
    submission_path = f"{file_path}.quiz_submission.json"
    try:
        with open(submission_path, "w", encoding="utf-8") as f:
            json.dump(submission.answers, f)
    except Exception as e:
        print(f"Failed to save quiz submission: {e}")

    return QuizEvaluationResponse(
        success=True,
        evaluation=None, # Evaluation happens in final report
        message="Round 1 complete. Your technical answers have been recorded for final evaluation."
    )
