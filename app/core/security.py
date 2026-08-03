"""
Security Module - JWT, Password Hashing, Token Management
Implements industry-standard authentication for API endpoints
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from app.core.config import settings
from fastapi import HTTPException, status, Header
import logging

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class JWTManager:
    """
    Manages JWT token creation, validation, and refresh token logic.
    """
    
    ALGORITHM = settings.JWT_ALGORITHM
    SECRET_KEY = settings.SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
    
    @classmethod
    def create_access_token(cls, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Dictionary containing claims (e.g., {"session_id": "..."})
            expires_delta: Optional custom expiration time
        
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire, "type": "access"})
        
        try:
            encoded_jwt = jwt.encode(
                to_encode,
                cls.SECRET_KEY,
                algorithm=cls.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create access token: {str(e)}")
            raise
    
    @classmethod
    def create_refresh_token(cls, data: Dict[str, Any]) -> str:
        """
        Create a JWT refresh token (longer expiration).
        
        Args:
            data: Dictionary containing claims
        
        Returns:
            Encoded refresh token
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            days=cls.REFRESH_TOKEN_EXPIRE_DAYS
        )
        to_encode.update({"exp": expire, "type": "refresh"})
        
        try:
            encoded_jwt = jwt.encode(
                to_encode,
                cls.SECRET_KEY,
                algorithm=cls.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create refresh token: {str(e)}")
            raise
    
    @classmethod
    def verify_token(cls, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Verify JWT token validity and decode claims.
        
        Args:
            token: JWT token string
            token_type: Expected token type ("access" or "refresh")
        
        Returns:
            Decoded claims dictionary if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                cls.SECRET_KEY,
                algorithms=[cls.ALGORITHM]
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return None


class PasswordManager:
    """
    Manages password hashing and verification using bcrypt.
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Password hashing failed: {str(e)}")
            raise
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.warning(f"Password verification error: {str(e)}")
            return False


class SessionSecurityManager:
    """
    Manages session security and access control.
    """
    
    @staticmethod
    def generate_session_token(session_id: str) -> str:
        """Generate a secure access token for a session."""
        return JWTManager.create_access_token(
            data={"session_id": session_id, "type": "session"}
        )
    
    @staticmethod
    def verify_session_token(token: str) -> Optional[str]:
        """
        Verify session token and return session ID.
        
        Returns:
            Session ID if token is valid, None otherwise
        """
        payload = JWTManager.verify_token(token, token_type="access")
        if payload and payload.get("type") == "session":
            return payload.get("session_id")
        return None


# =====================================================
# FastAPI Dependency for Protected Routes
# =====================================================

async def verify_token_dependency(authorization: Optional[str] = Header(None)) -> str:
    """
    FastAPI dependency to verify JWT token from Authorization header.
    
    Usage in endpoints:
        @router.post("/protected-endpoint")
        async def protected_route(session_id: str = Depends(verify_token_dependency)):
            # session_id is guaranteed to be valid
            return {"session_id": session_id}
    
    Raises:
        HTTPException(401): If token is missing, expired, or invalid
        HTTPException(403): If token format is incorrect
    
    Returns:
        Session ID from valid token
    """
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Expected format: "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning(f"Invalid Authorization header format: {parts}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Authorization header. Expected: 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = parts[1]
    
    # Verify token
    session_id = SessionSecurityManager.verify_session_token(token)
    if not session_id:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return session_id
