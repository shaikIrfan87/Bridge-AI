"""
Models Package
"""

from app.models.upload import FileInfo, UploadResponse, ErrorResponse
from app.models.skills import CandidateProfile, AnalysisResponse
from app.models.quiz import Quiz, Question, QuizResponse
from app.models.coding import CodingChallenge, CodeSubmission, EvaluationResult
from app.models.report import ReportRequest, FinalReport, ReportResponse

__all__ = [
    "FileInfo", 
    "UploadResponse", 
    "ErrorResponse",
    "CandidateProfile",
    "AnalysisResponse",
    "Quiz",
    "Question",
    "QuizResponse",
    "CodingChallenge",
    "CodeSubmission",
    "EvaluationResult",
    "ReportRequest",
    "FinalReport",
    "ReportResponse"
]
