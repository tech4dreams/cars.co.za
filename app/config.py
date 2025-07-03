# Simple configuration management for Cars.co.za Sentiment API

import os
from dotenv import load_dotenv
from typing import List, Optional

# Load environment variables
load_dotenv()

class Settings:
    # API Configuration
    app_name: str = "Cars.co.za Sentiment API"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Server Configuration
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # CORS Configuration
    allowed_origins: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8080",  # Vue dev server
        "https://yourdomain.com",  # Production frontend
        "*"  # Remove this in production
    ]
    
    # API Keys
    cohere_api_key: str = os.getenv("COHERE_API_KEY", "")
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "")
    
    # YouTube API Configuration
    youtube_api_base_url: str = "https://www.googleapis.com/youtube/v3"
    max_comments_per_video: int = int(os.getenv("MAX_COMMENTS", "100"))
    
    # NLP Configuration
    sentiment_model: str = os.getenv("SENTIMENT_MODEL", "cardiffnlp/twitter-roberta-base-sentiment")
    cohere_model: str = os.getenv("COHERE_MODEL", "command-r")
    max_comment_length: int = int(os.getenv("MAX_COMMENT_LENGTH", "500"))
    
    # Rate Limiting
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour in seconds
    
    # Database (if you plan to add one later)
    database_url: Optional[str] = os.getenv("DATABASE_URL")
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: Optional[str] = os.getenv("LOG_FILE")
    
    # Cache Configuration (if you plan to add Redis later)
    redis_url: Optional[str] = os.getenv("REDIS_URL")
    cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    
    # Model Configuration
    model_cache_dir: str = os.getenv("MODEL_CACHE_DIR", "./models")

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
    
    if settings.secret_key == "your-secret-key-change-this-in-production":
        errors.append("SECRET_KEY should be changed in production")
    
    if errors:
        print(f"Configuration warnings: {', '.join(errors)}")
        # Don't raise error, just warn
    
    return True

# Environment-specific configurations
def get_cors_origins():
    """Get CORS origins based on environment"""
    if settings.debug:
        return ["*"]  # Allow all origins in development
    else:
        return [origin for origin in settings.allowed_origins if origin != "*"]

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
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["default"],
        },
    }

# Model paths and configurations
MODEL_CONFIGS = {
    "sentiment": {
        "model_name": settings.sentiment_model,
        "cache_dir": f"{settings.model_cache_dir}/sentiment",
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
        "captions": f"{settings.youtube_api_base_url}/captions",
    }
}