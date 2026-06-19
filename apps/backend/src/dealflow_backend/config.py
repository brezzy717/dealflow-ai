from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://dealflow:dealflow@localhost:5432/dealflow"
)


class Settings(BaseSettings):
    """Application configuration sourced from environment variables."""

    environment: str = Field(default="development", alias="ENVIRONMENT")
    database_url: str = Field(
        default=INSECURE_DEFAULT_DATABASE_URL,
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    service_name: str = Field(default="dealflow-backend")
    api_prefix: str = Field(default="/api")
    docs_url: str = Field(default="/docs")
    openapi_url: str = Field(default="/openapi.json")
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        alias="CORS_ALLOW_ORIGINS",
    )
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")

    @model_validator(mode="after")
    def _reject_insecure_defaults_in_production(self) -> "Settings":
        """Fail fast if production is left on the local development defaults."""
        if (
            self.environment == "production"
            and self.database_url == INSECURE_DEFAULT_DATABASE_URL
        ):
            raise ValueError(
                "DATABASE_URL must be set explicitly in production; "
                "the local development default is not permitted."
            )
        return self

    model_config = SettingsConfigDict(
        env_file=[
            Path(__file__).resolve().parents[3] / ".env",
            Path(__file__).resolve().parents[3] / "configs" / "env" / "backend.env",
        ],
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


settings = get_settings()
