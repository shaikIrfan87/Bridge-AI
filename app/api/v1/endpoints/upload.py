"""
Resume Upload Endpoint
CHUNK 1.2 - File upload with validation
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import os
from app.models.upload import UploadResponse, ErrorResponse, FileInfo
from app.utils.file_handler import (
    FileValidator,
    FileStorage,
    generate_session_id,
    get_file_size_mb
)
from app.utils.text_extractor import TextExtractor

router = APIRouter()


@router.post("/upload-resume", response_model=UploadResponse)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF or DOCX)")
):
    """
    Upload resume file
    
    - Validates file type (PDF, DOCX)
    - Validates file size (max 10MB)
    - Saves file to temporary storage
    - Returns session ID for tracking
    
    **Validation Rules:**
    - Allowed formats: PDF (.pdf), DOCX (.docx)
    - Maximum size: 10MB
    - Filename sanitization applied
    """
    
    try:
        # Validate file type
        is_valid_type, type_error = FileValidator.validate_file_type(file.filename)
        if not is_valid_type:
            raise HTTPException(status_code=400, detail=type_error)
        
        # Read file to get size
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        is_valid_size, size_error = FileValidator.validate_file_size(file_size)
        if not is_valid_size:
            raise HTTPException(status_code=400, detail=size_error)
        
        # Reset file pointer
        await file.seek(0)
        
        # Sanitize filename
        safe_filename = FileValidator.sanitize_filename(file.filename)
        
        # Save file
        file_path, unique_filename = await FileStorage.save_upload_file(file)
        
        # SQLite Persistence
        from app.core.database import AssessmentSession, engine
        from sqlmodel import Session
        
        session_id = unique_filename # Use the unique filename as session ID for consistency
        
        with Session(engine) as db_session:
            db_record = AssessmentSession(
                id=session_id,
                filename=unique_filename,
                original_name=safe_filename,
                created_at=datetime.utcnow()
            )
            db_session.add(db_record)
            db_session.commit()
        
        # Get file extension
        file_extension = FileValidator.get_file_extension(file.filename)
        
        # CHUNK 1.3: Extract Text
        extracted_text = ""
        try:
            extracted_text = TextExtractor.extract_text(file_path, file_extension)
            
            # Save extracted text to sidecar file
            text_file_path = f"{file_path}.txt"
            with open(text_file_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)
                
        except Exception as e:
            # We don't want to fail the upload if extraction fails, but we should note it
            print(f"Text extraction failed: {e}")
            extracted_text = f"Error extracting text: {str(e)}"

        # Create file info (Don't return internal file_path for security)
        file_info = FileInfo(
            filename=unique_filename,
            original_filename=safe_filename,
            size_bytes=file_size,
            size_mb=get_file_size_mb(file_size),
            file_type=file_extension.upper(),
            upload_timestamp=datetime.utcnow().isoformat(),
            file_path=None
        )
        
        return UploadResponse(
            success=True,
            message=f"Resume uploaded & parsed successfully ({file_info.size_mb}MB)",
            file_info=file_info,
            session_id=session_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/upload-status")
async def upload_status():
    """
    Get upload endpoint status
    Returns allowed file types and size limits
    """
    from app.core import settings
    
    return {
        "status": "ready",
        "allowed_formats": settings.allowed_extensions_list,
        "max_size_mb": settings.MAX_FILE_SIZE_MB,
        "endpoint": "/api/v1/upload-resume",
        "method": "POST"
    }
