"""
Report Endpoints
"""

import os
import json
from fastapi import APIRouter, HTTPException, Depends
from app.services.report_generator import ReportGenerator
from app.models.report import ReportRequest, ReportResponse, FinalReport
from app.utils.file_handler import FileStorage as FileHandler

router = APIRouter()


@router.post("/generate-report", response_model=ReportResponse)
async def generate_report_endpoint(
    request: ReportRequest
):
    """
    Generate the final comprehensive candidate evaluation report.
    Synthesizes resume profile, quiz performance, and coding challenge scores.
    """
    filename = request.filename
    if not filename or os.path.basename(filename) != filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    upload_dir = FileHandler.get_upload_dir()
    file_path = os.path.join(upload_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Session file not found. Please upload your resume again.")

    # Validate profile exists
    profile_path = f"{file_path}.json"
    if not os.path.exists(profile_path):
        raise HTTPException(
            status_code=422,
            detail="Resume analysis not found. Please analyze your resume before generating a report."
        )

    # NEW: Deferred Bulk Evaluation
    report = await ReportGenerator.evaluate_and_generate_report(
        file_path=file_path,
        filename=filename
    )

    if not report:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate report. Please try again."
        )

    # Auto-delete files
    import glob
    for f in glob.glob(f"{file_path}*"):
        try:
            os.remove(f)
        except:
            pass

    return ReportResponse(
        success=True,
        report=report,
        message=f"Report generated successfully — Verdict: {report.recommendation.verdict}"
    )


@router.post("/record-cheat")
async def record_cheat_endpoint(request: ReportRequest):
    """
    Mark a session as 'Cheated' and fail the assessment immediately.
    Called when the candidate attempts to switch tabs or minimize the assessment window.
    """
    filename = request.filename
    upload_dir = FileHandler.get_upload_dir()
    file_path = os.path.join(upload_dir, filename)
    with open(f"{file_path}.cheated", "w") as f:
        f.write("cheated")
    
    return {"success": True, "message": "Integrity violation recorded. Assessment terminated."}
