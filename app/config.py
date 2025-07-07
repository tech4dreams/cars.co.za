# Production-ready configuration for Cars.co.za Sentiment API
# app/config.py (deployment version)

import os
import secrets
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
    
    # CORS Configuration - More restrictive for production
    allowed_origins: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:3001",  # Alternative React dev
        "http://localhost:8080",  # Vue dev server
        "https://cars.co.za",     # Production domain
        "https://www.cars.co.za", # Production domain with www
        os.getenv("FRONTEND_URL", ""),  # Dynamic frontend URL
    ]
    
    # Remove empty strings and wildcards for production
    allowed_origins = [origin for origin in allowed_origins if origin and origin != "*"]
    
    # API Keys
    cohere_api_key: str = os.getenv("COHERE_API_KEY", "")
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "")
    
    # YouTube API Configuration
    youtube_api_base_url: str = "https://www.googleapis.com/youtube/v3"
    max_comments_per_video: int = int(os.getenv("MAX_COMMENTS", "200"))  # Increased for production
    
    # NLP Configuration - Cloud-only
    sentiment_model: str = "cohere"  # Use Cohere instead of local models
    cohere_model: str = os.getenv("COHERE_MODEL", "command-r")
    max_comment_length: int = int(os.getenv("MAX_COMMENT_LENGTH", "500"))
    
    # Rate Limiting
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour
    
    # Database (future use)
    database_url: Optional[str] = os.getenv("DATABASE_URL")
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: Optional[str] = os.getenv("LOG_FILE")
    
    # Cache Configuration
    redis_url: Optional[str] = os.getenv("REDIS_URL")
    cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
    
    # Security - Generate secure secret key if not provided
    secret_key: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    
    # Performance Settings
    max_concurrent_requests: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "300"))  # 5 minutes
    
    # Feature Flags
    enable_transcript_analysis: bool = os.getenv("ENABLE_TRANSCRIPT_ANALYSIS", "True").lower() == "true"
    enable_detailed_categories: bool = os.getenv("ENABLE_DETAILED_CATEGORIES", "True").lower() == "true"
    enable_ai_report: bool = os.getenv("ENABLE_AI_REPORT", "True").lower() == "true"

# Create settings instance
settings = Settings()

# Enhanced validation function
def validate_settings():
    """Validate critical settings on startup"""
    errors = []
    warnings = []
    
    # Critical errors
    if not settings.cohere_api_key:
        errors.append("COHERE_API_KEY is required for sentiment analysis")
    
    if not settings.youtube_api_key:
        errors.append("YOUTUBE_API_KEY is required for video data")
    
    # Warnings
    if settings.secret_key == "your-secret-key-change-this-in-production":
        warnings.append("SECRET_KEY should be changed in production")
    
    if settings.debug and not any("localhost" in origin for origin in settings.allowed_origins):
        warnings.append("Debug mode is enabled but no localhost origins configured")
    
    if not settings.debug and "*" in settings.allowed_origins:
        warnings.append("Wildcard CORS origin detected in production mode")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    if warnings:
        print(f"⚠️  Configuration warnings: {', '.join(warnings)}")
    
    return True

# Environment-specific configurations
def get_cors_origins():
    """Get CORS origins based on environment"""
    if settings.debug:
        # In development, allow localhost origins
        dev_origins = [
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080"
        ]
        return dev_origins + [origin for origin in settings.allowed_origins if "localhost" not in origin]
    else:
        # In production, only allow specified origins
        return [origin for origin in settings.allowed_origins if origin and origin != "*"]

def get_log_config():
    """Get logging configuration with more details for production"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "detailed" if not settings.debug else "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["default"],
        },
        "loggers": {
            "uvicorn": {
                "level": "INFO",
                "handlers": ["default"],
                "propagate": False,
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["default"],
                "propagate": False,
            },
        },
    }

# API endpoints configuration
API_ENDPOINTS = {
    "youtube": {
        "comments": f"{settings.youtube_api_base_url}/commentThreads",
        "videos": f"{settings.youtube_api_base_url}/videos",
        "captions": f"{settings.youtube_api_base_url}/captions",
    },
    "cohere": {
        "chat": "https://api.cohere.ai/v1/chat",
    }
}

# Health check configuration
HEALTH_CHECK = {
    "app_name": settings.app_name,
    "version": settings.app_version,
    "environment": "development" if settings.debug else "production",
    "dependencies": {
        "youtube_api": bool(settings.youtube_api_key),
        "cohere_api": bool(settings.cohere_api_key),
    }
}