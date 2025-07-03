# Configuration management for Cars.co.za Sentiment API

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import List

# Load environment variables
load_dotenv("C:/Users/Seth.Valentine/cars.co.za/.env")

class Settings(BaseSettings):
    # API Configuration
    app_name: str = "Cars.co.za Sentiment API"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"

    # Server Configuration
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # CORS Configuration
    allowed_origins: List[str] = [
        "http://localhost:3000",  # React dev server
        "https://cars-coza-frontend.vercel.app",  # Replace with deployed front-end URL
    ]

    # API Keys
    cohere_api_key: str = os.getenv("COHERE_API_KEY", "")
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "")

    # YouTube API Configuration
    youtube_api_base_url: str = "https://www.googleapis.com/youtube/v3"
    max_comments_per_video: int = int(os.getenv("MAX_COMMENTS", "100"))

    # NLP Configuration
    sentiment_model: str = os.getenv(
        "SENTIMENT_MODEL", "distilbert-base-uncased-finetuned-sst-2-english"
    )
    cohere_model: str = os.getenv("COHERE_MODEL", "command")
    max_comment_length: int = int(os.getenv("MAX_COMMENT_LENGTH", "512"))

    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "uvicorn.log")

    class Config:
        env_file = "C:/Users/Seth.Valentine/cars.co.za/.env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Create settings instance
settings = Settings()

# Validation function
def validate_settings():
    """Validate critical settings on startup"""
    errors = []
    if not settings.cohere_api_key:
        errors.append("COHERE_API_KEY is required")
    if not settings.youtube_api_key:
        errors.append("YOUTUBE_API_KEY is required")
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    return True

# Environment-specific configurations
def get_cors_origins():
    """Get CORS origins based on environment"""
    if settings.debug:
        return ["*"]  # Allow all origins in development
    return settings.allowed_origins

def get_log_config():
    """Get logging configuration"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "formatter": "default",
                "class": "logging.FileHandler",
                "filename": settings.log_file,
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["default", "file"],
        },
    }

# Model paths and configurations
MODEL_CONFIGS = {
    "sentiment": {
        "model_name": settings.sentiment_model,
        "cache_dir": "./models/sentiment",
    },
    "cohere": {
        "model_name": settings.cohere_model,
        "api_key": settings.cohere_api_key,
    }
}

# API endpoints configuration
API_ENDPOINTS = {
    "youtube": {
        "comments": f"{settings.youtube_api_base_url}/commentThreads",
        "videos": f"{settings.youtube_api_base_url}/videos",
    }
}