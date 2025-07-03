from fastapi import FastAPI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

try:
    from app.sentiment import sentiment_router
    app.include_router(sentiment_router, prefix="/analyze")
except ImportError as e:
    logger.error(f"Failed to import sentiment_router: {e}")
    raise

try:
    from app.youtube import youtube_router
    app.include_router(youtube_router)
except ImportError as e:
    logger.error(f"Failed to import youtube_router: {e}")
    raise

try:
    from app.full_report import full_report_router
    app.include_router(full_report_router, prefix="/analyze")
except ImportError as e:
    logger.error(f"Failed to import full_report_router: {e}")
    raise