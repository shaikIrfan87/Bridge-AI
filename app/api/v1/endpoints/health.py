"""
Health Check Endpoint
Used to verify server is running and responsive
"""

from fastapi import APIRouter
from datetime import datetime
from app.core import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns server status and basic info
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "development" if settings.API_DEBUG else "production"
    }


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint
    Ultra-lightweight check
    """
    return {"message": "pong"}
