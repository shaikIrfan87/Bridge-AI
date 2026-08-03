"""
Connection Test Endpoint
Tests backend-frontend integration
"""

from fastapi import APIRouter
from datetime import datetime
from app.core import settings
import platform
import sys

router = APIRouter()


@router.get("/connection-test")
async def connection_test():
    """
    Comprehensive connection test
    Returns detailed system and connection info
    """
    return {
        "status": "connected",
        "timestamp": datetime.utcnow().isoformat(),
        "backend": {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": platform.system(),
            "host": settings.API_HOST,
            "port": settings.API_PORT,
            "debug": settings.API_DEBUG,
        },
        "cors": {
            "allowed_origins": settings.allowed_origins_list,
            "configured": True
        },
        "endpoints": {
            "health": "/api/v1/health",
            "connection_test": "/api/v1/connection-test",
            "ping": "/api/v1/ping",
            "docs": "/docs",
            "frontend": "/"
        },
        "message": "Backend and frontend are perfectly connected! 🚀"
    }


@router.get("/test-cors")
async def test_cors():
    """
    Test CORS configuration
    """
    return {
        "cors_enabled": True,
        "allowed_origins": settings.allowed_origins_list,
        "message": "CORS is properly configured"
    }
