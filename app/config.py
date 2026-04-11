"""Application configuration and settings"""
import os
from typing import List
from pydantic_settings import BaseSettings

_INSECURE_JWT_DEFAULT = "your-secret-key-change-in-production"


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://ogmywbnbcurwhkpuqhku.supabase.co")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # JWT Configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", _INSECURE_JWT_DEFAULT)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Vet Clinic VMS"

    # CORS — comma-separated list of allowed origins, e.g.
    # "http://localhost:8080,https://app.miavet.com"
    FRONTEND_ORIGINS: str = os.getenv("FRONTEND_ORIGINS", "http://localhost:8080")

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.FRONTEND_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def validate_settings() -> None:
    """Fail fast on insecure or missing required settings."""
    if settings.JWT_SECRET == _INSECURE_JWT_DEFAULT:
        raise RuntimeError(
            "JWT_SECRET is set to the insecure default. "
            "Set JWT_SECRET in .env to a strong random value before starting."
        )
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY is not set. "
            "The backend requires the service role key to bypass RLS."
        )
    if not settings.SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL is not set.")
