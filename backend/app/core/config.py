"""
Centralized application configuration.

All environment-dependent values MUST be read here and nowhere else.
This is the single source of truth for settings, loaded from environment
variables (see .env.example for the full list of supported keys).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App metadata ---
    app_name: str = "LifeOS Backend"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"

    # --- CORS ---
    cors_origins: str = "http://localhost:3000"

    # --- Database ---
    database_url: str = "postgresql+psycopg2://lifeos:lifeos@localhost:5432/lifeos"

    # --- Auth (JWT) ---
    jwt_secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance - avoids re-reading env on every request."""
    return Settings()
