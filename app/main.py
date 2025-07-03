# Entry point

from fastapi import FastAPI
from app.youtube import router as youtube_router
from app.sentiment import router as sentiment_router
from fastapi.middleware.cors import CORSMiddleware
import logging.config
from app.config import settings, validate_settings, get_cors_origins, get_log_config

# Configure logging
logging.config.dictConfig(get_log_config())
logger = logging.getLogger(__name__)

# Validate configuration on startup
try:
    validate_settings()
    logger.info("Configuration validation passed")
except Exception as e:
    logger.warning(f"Configuration validation issues: {e}")
    # Continue anyway for development

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
app.include_router(youtube_router, prefix="/youtube", tags=["YouTube"])
app.include_router(sentiment_router, prefix="/analyze", tags=["Sentiment"])

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
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )