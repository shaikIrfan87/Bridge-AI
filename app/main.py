from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.core import settings
from app.api.v1.router import api_router
from app.utils.file_handler import FileStorage
import os
import logging
import time

# Configure Rugged Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("clinxai.core")

def create_application() -> FastAPI:
    """
    Fortified Application Factory
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.API_DEBUG,
    )
    
    # 🏁 Startup: Environment Sanitizer
    @app.on_event("startup")
    async def on_startup():
        logger.info("Initializing ClinXAI Self-Healing Engine...")
        try:
            # Ensure upload directories exist
            upload_dir = FileStorage.get_upload_dir()
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir, exist_ok=True)
                logger.info(f"Created missing upload directory: {upload_dir}")
            
            # Initialize Database with Rugged Fallback
            from app.core.database import init_db
            init_db()
            logger.info("Database Synchronized.")
        except Exception as e:
            logger.error(f"STARTUP FAILURE: {str(e)}")

    # 🛡️ Global Disaster Recovery Middleware
    @app.middleware("http")
    async def global_exception_monitor(request: Request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(f"{request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"CRITICAL ERROR on {request.url.path}: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "The system encountered a logic error. Our engineering team has been notified.",
                    "error": str(e) if settings.API_DEBUG else "Internal Integrity Error"
                }
            )

    # CORS Middleware (Locked Down)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Final Routing
    app.include_router(api_router, prefix="/api/v1")
    
    # Static Assets & Catch-all SPA logic
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    
    @app.get("/")
    async def get_root():
        index_path = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"status": "Backend Active", "frontend": "Missing - Place HTML in /frontend"}
    
    # Serve Frontend automatically
    if os.path.exists(frontend_dir):
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    
    return app

# Master Instance
app = create_application()
