"""
Application configuration using Pydantic Settings.
Loads from environment variables and .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "FHIR Patient Portal"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # SMART on FHIR
    EPIC_CLIENT_ID: str
    EPIC_REDIRECT_URI: str = "http://localhost:8000/auth/callback"

    # Used as the `aud` parameter in the authorization request
    EPIC_FHIR_BASE_URL: str = "https://launch.smarthealthit.org/v/r4/sim/eyJhIjoiMSJ9/fhir"

    # Used for actual FHIR API calls in the proxy
    EPIC_FHIR_API_URL: str = "https://r4.smarthealthit.org"

    EPIC_AUTH_URL: str = "https://launch.smarthealthit.org/v/r4/sim/eyJhIjoiMSJ9/auth/authorize"
    EPIC_TOKEN_URL: str = "https://launch.smarthealthit.org/v/r4/sim/eyJhIjoiMSJ9/auth/token"

    REDIS_URL: str = "redis://localhost:6379"

    FRONTEND_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Create settings instance
settings = Settings()