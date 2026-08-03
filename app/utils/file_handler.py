"""
File Upload Utilities
Validation, storage, and helper functions
"""

import os
import uuid
from datetime import datetime
from typing import Tuple, Optional
from fastapi import UploadFile
from app.core import settings


class FileValidator:
    """
    File validation utilities
    Validates file type, size, and security
    """
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Extract file extension"""
        return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    @staticmethod
    def validate_file_type(filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file type against allowed extensions
        Returns: (is_valid, error_message)
        """
        extension = FileValidator.get_file_extension(filename)
        
        if not extension:
            return False, "File has no extension"
        
        allowed = settings.allowed_extensions_list
        if extension not in allowed:
            return False, f"Invalid file type. Allowed: {', '.join(allowed)}"
        
        return True, None
    
    @staticmethod
    def validate_file_size(size_bytes: int) -> Tuple[bool, Optional[str]]:
        """
        Validate file size against maximum allowed
        Returns: (is_valid, error_message)
        """
        max_size = settings.max_file_size_bytes
        
        if size_bytes > max_size:
            size_mb = size_bytes / (1024 * 1024)
            max_mb = settings.MAX_FILE_SIZE_MB
            return False, f"File too large ({size_mb:.2f}MB). Maximum: {max_mb}MB"
        
        if size_bytes == 0:
            return False, "File is empty"
        
        return True, None
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent security issues
        - Remove path separators
        - Remove special characters
        - Limit length
        """
        # Remove directory paths
        filename = os.path.basename(filename)
        
        # Keep only alphanumeric, dots, hyphens, underscores
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in '.-_':
                safe_chars.append(char)
            else:
                safe_chars.append('_')
        
        sanitized = ''.join(safe_chars)
        
        # Limit length (keep extension)
        if len(sanitized) > 100:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:95] + ext
        
        return sanitized


class FileStorage:
    """
    File storage utilities
    Handles saving files to disk
    """
    
    @staticmethod
    def get_upload_dir() -> str:
        """Get or create upload directory"""
        upload_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "uploads"
        )
        
        os.makedirs(upload_dir, exist_ok=True)
        return upload_dir
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """
        Generate unique filename using UUID
        Preserves original extension
        """
        extension = FileValidator.get_file_extension(original_filename)
        unique_id = uuid.uuid4().hex
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        return f"{timestamp}_{unique_id}.{extension}"
    
    @staticmethod
    async def save_upload_file(file: UploadFile) -> Tuple[str, str]:
        """
        Save uploaded file to disk
        Returns: (file_path, unique_filename)
        """
        upload_dir = FileStorage.get_upload_dir()
        unique_filename = FileStorage.generate_unique_filename(file.filename)
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Write file in chunks to handle large files
        chunk_size = 1024 * 1024  # 1MB chunks
        
        with open(file_path, 'wb') as f:
            while chunk := await file.read(chunk_size):
                f.write(chunk)
        
        return file_path, unique_filename


def generate_session_id() -> str:
    """Generate unique session ID for tracking"""
    return f"session_{uuid.uuid4().hex[:16]}"


def get_file_size_mb(size_bytes: int) -> float:
    """Convert bytes to MB"""
    return round(size_bytes / (1024 * 1024), 2)
