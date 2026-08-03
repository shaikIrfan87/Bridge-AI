"""
Authentication Models
Defines token and user data structures
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TokenResponse(BaseModel):
    """Response model for token endpoints"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until expiration


class SessionTokenData(BaseModel):
    """Session authentication token data"""
    session_id: str
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """JWT token payload structure"""
    session_id: Optional[str] = None
    exp: Optional[datetime] = None
    type: str = "access"


class SessionAuth(BaseModel):
    """Session authentication request"""
    session_id: str


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token"""
    refresh_token: str
