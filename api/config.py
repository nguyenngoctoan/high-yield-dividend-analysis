"""
Configuration management for the Dividend API.

Loads configuration from environment variables with sensible defaults.
"""

import os
import logging
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logger
logger = logging.getLogger(__name__)


class Settings:
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Dividend API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Database
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
    GOOGLE_AUTH_URI: str = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URI: str = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URI: str = "https://www.googleapis.com/oauth2/v3/userinfo"

    # JWT and Sessions
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    def __init__(self):
        """Validate configuration on initialization"""
        # Production security validation
        if self.is_production:
            # Validate SECRET_KEY
            if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be set and at least 32 characters in production. "
                    "Generate with: openssl rand -hex 32"
                )
            if self.SECRET_KEY == "change-this-secret-key-in-production":
                raise ValueError("SECRET_KEY cannot use default value in production")

            # Validate SESSION_SECRET
            if not self.SESSION_SECRET or len(self.SESSION_SECRET) < 32:
                raise ValueError(
                    "SESSION_SECRET must be set and at least 32 characters in production. "
                    "Generate with: openssl rand -hex 32"
                )
            if self.SESSION_SECRET == "change-this-session-secret-in-production":
                raise ValueError("SESSION_SECRET cannot use default value in production")

            # Validate CORS
            if "*" in self.ALLOWED_ORIGINS:
                raise ValueError(
                    "ALLOWED_ORIGINS cannot contain '*' in production. "
                    "Specify exact origins: https://yourdomain.com"
                )

        # Use development defaults only in development
        if not self.SECRET_KEY:
            if self.is_production:
                raise ValueError("SECRET_KEY is required")
            else:
                self.SECRET_KEY = "development-insecure-secret-key-change-in-production"
                logger.warning("⚠️  Using insecure default SECRET_KEY for development")

        if not self.SESSION_SECRET:
            if self.is_production:
                raise ValueError("SESSION_SECRET is required")
            else:
                self.SESSION_SECRET = "development-insecure-session-secret-change-in-production"
                logger.warning("⚠️  Using insecure default SESSION_SECRET for development")

    # CORS
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8000"
    ).split(",")

    # Security
    COOKIE_DOMAIN: str = os.getenv("COOKIE_DOMAIN", "localhost")
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"


# Global settings instance
settings = Settings()
