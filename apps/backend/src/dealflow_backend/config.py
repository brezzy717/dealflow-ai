from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration sourced from environment variables."""

    environment: str = Field(default="development", alias="ENVIRONMENT")
    database_url: str = Field(
        default="postgresql+asyncpg://dealflow:dealflow@localhost:5432/dealflow",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    service_name: str = Field(default="dealflow-backend")
    api_prefix: str = Field(default="/api")
    docs_url: str = Field(default="/docs")
    openapi_url: str = Field(default="/openapi.json")
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")

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
