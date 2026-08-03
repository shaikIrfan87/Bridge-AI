"""
Configuration Management using Pydantic Settings
Loads environment variables and provides type-safe config access
"""

from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """
    Application Settings - loads from .env file
    All values are type-validated by Pydantic
    """
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 19440
    API_DEBUG: bool = True  # Changed to True for development
    API_RELOAD: bool = True  # Enabled for development reload
    
    # Security
    SECRET_KEY: str = "dev-secret-key-replace-in-production-with-random-string"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:19440"
    
    # JWT Configuration
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Gemini AI (will be used in CHUNK 2.1)
    GEMINI_API_KEY: str = ""
    
    # File Upload Limits (will be used in CHUNK 1.2)
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "pdf,docx"
    
    # Code Execution
    CODE_TIMEOUT_SECONDS: int = 5
    MAX_CODE_OUTPUT_LENGTH: int = 5000
    
    # Application Metadata
    APP_NAME: str = "Skill Assessment System"
    APP_VERSION: str = "1.0.0"
    
    class Config:
        # Find .env file relative to project root
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = True
        env_file_encoding = 'utf-8'
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Convert comma-separated extensions to list"""
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes"""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


# Global settings instance
settings = Settings()
