"""
Configuration management for the Dividend API.

Loads configuration from environment variables with sensible defaults.
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


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
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "change-this-session-secret-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

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

    def validate(self) -> None:
        """Validate required configuration values."""
        errors = []

        if not self.SUPABASE_URL:
            errors.append("SUPABASE_URL is required")
        if not self.SUPABASE_KEY:
            errors.append("SUPABASE_KEY is required")
        if not self.GOOGLE_CLIENT_ID:
            errors.append("GOOGLE_CLIENT_ID is required for OAuth")
        if not self.GOOGLE_CLIENT_SECRET:
            errors.append("GOOGLE_CLIENT_SECRET is required for OAuth")
        if self.SECRET_KEY == "change-this-secret-key-in-production" and self.is_production:
            errors.append("SECRET_KEY must be changed in production")
        if self.SESSION_SECRET == "change-this-session-secret-in-production" and self.is_production:
            errors.append("SESSION_SECRET must be changed in production")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")


# Global settings instance
settings = Settings()
