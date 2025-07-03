from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings, validate_settings, get_cors_origins, get_log_config
import logging.config

# Configure logging
logging.config.dictConfig(get_log_config())
logger = logging.getLogger(__name__)

# Validate configuration on startup
try:
    validate_settings()
    logger.info("Configuration validation passed")
except ValueError as e:
    logger.error(f"Configuration validation failed: {e}")
    # In production, consider exiting: import sys; sys.exit(1)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="API for analyzing YouTube video sentiment and engagement"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
try:
    from app.sentiment import sentiment_router
    app.include_router(sentiment_router, prefix="/analyze", tags=["Sentiment"])
except ImportError as e:
    logger.error(f"Failed to import sentiment_router: {e}")
    raise

try:
    from app.youtube import youtube_router
    app.include_router(youtube_router, prefix="/youtube", tags=["YouTube"])
except ImportError as e:
    logger.error(f"Failed to import youtube_router: {e}")
    raise

try:
    from app.full_report import full_report_router
    app.include_router(full_report_router, prefix="/analyze", tags=["Full Report"])
except ImportError as e:
    logger.error(f"Failed to import full_report_router: {e}")
    raise

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )