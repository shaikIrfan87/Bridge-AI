"""
File Upload Models
Pydantic models for file upload responses
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FileInfo(BaseModel):
    """File information model"""
    filename: str
    original_filename: str
    size_bytes: int
    size_mb: float
    file_type: str
    upload_timestamp: str
    file_path: Optional[str] = None


class UploadResponse(BaseModel):
    """Response model for file upload"""
    success: bool
    message: str
    file_info: Optional[FileInfo] = None
    session_id: str


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    details: Optional[str] = None
