"""
Authentication Endpoints - Login, Token Refresh, Session Management
Provides secure access to assessment sessions
"""

from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime, timedelta
from app.core.security import JWTManager, SessionSecurityManager
from app.core.database import SessionToken, AssessmentSession, engine
from app.models.auth import TokenResponse, SessionTokenData, SessionAuth
from sqlmodel import Session, select
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/session-token", response_model=SessionTokenData)
async def get_session_token(request: SessionAuth):
    """
    Generate an access token for a specific assessment session.
    
    This endpoint provides authentication-based access control to sessions.
    Only users with valid tokens can access their assessment data.
    
    Args:
        request: SessionAuth with session_id
    
    Returns:
        SessionTokenData with access token (valid for 30 minutes)
    """
    try:
        # Validate session exists
        with Session(engine) as db_session:
            statement = select(AssessmentSession).where(
                AssessmentSession.id == request.session_id
            )
            session = db_session.exec(statement).first()
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            # Generate token
            access_token = SessionSecurityManager.generate_session_token(request.session_id)
            
            # Store token in database
            token_record = SessionToken(
                session_id=request.session_id,
                user_id=session.user_id,
                access_token=access_token,
                expires_at=datetime.utcnow() + timedelta(minutes=30),
                is_valid=True
            )
            db_session.add(token_record)
            db_session.commit()
            
            return SessionTokenData(
                session_id=request.session_id,
                access_token=access_token,
                expires_in=30 * 60  # 30 minutes in seconds
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate token"
        )


@router.post("/verify-token")
async def verify_token(token: str) -> dict:
    """
    Verify a session token.
    
    Args:
        token: JWT access token
    
    Returns:
        Dictionary with session_id if valid
    """
    session_id = SessionSecurityManager.verify_session_token(token)
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Verify token is still valid in database
    with Session(engine) as db_session:
        statement = select(SessionToken).where(
            SessionToken.access_token == token,
            SessionToken.is_valid == True
        )
        token_record = db_session.exec(statement).first()
        
        if not token_record or token_record.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
    
    return {
        "valid": True,
        "session_id": session_id
    }


@router.post("/invalidate-token")
async def invalidate_token(token: str) -> dict:
    """
    Invalidate a token (logout).
    
    Marks the token as invalid in the database.
    """
    try:
        with Session(engine) as db_session:
            statement = select(SessionToken).where(
                SessionToken.access_token == token
            )
            token_record = db_session.exec(statement).first()
            
            if token_record:
                token_record.is_valid = False
                db_session.add(token_record)
                db_session.commit()
        
        return {"success": True, "message": "Token invalidated"}
    
    except Exception as e:
        logger.error(f"Token invalidation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate token"
        )


def get_current_session_id(token: str) -> str:
    """
    Dependency to extract and verify session ID from token.
    Used in protected endpoints.
    """
    session_id = SessionSecurityManager.verify_session_token(token)
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Verify session exists and token is valid in database
    with Session(engine) as db_session:
        session_statement = select(AssessmentSession).where(
            AssessmentSession.id == session_id
        )
        session = db_session.exec(session_statement).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        token_statement = select(SessionToken).where(
            SessionToken.access_token == token,
            SessionToken.is_valid == True,
            SessionToken.expires_at >= datetime.utcnow()
        )
        token_record = db_session.exec(token_statement).first()
        
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired or invalid"
            )
    
    return session_id
