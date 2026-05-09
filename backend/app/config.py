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
    
    # Epic SMART on FHIR
    EPIC_CLIENT_ID: str
    EPIC_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    EPIC_FHIR_BASE_URL: str = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
    EPIC_AUTH_URL: str = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize"
    EPIC_TOKEN_URL: str = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"

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