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
    model_artifacts_dir: str = Field(default="artifacts", alias="MODEL_ARTIFACTS_DIR")

    # Clerk auth (JWT verification). JWKS URL + issuer are required to enforce
    # auth; audience is optional. See dealflow_backend/auth/clerk.py.
    clerk_jwks_url: str | None = Field(default=None, alias="CLERK_JWKS_URL")
    clerk_issuer: str | None = Field(default=None, alias="CLERK_ISSUER")
    clerk_audience: str | None = Field(default=None, alias="CLERK_AUDIENCE")

    # Billing webhook shared secret (stand-in for Stripe signature verification).
    billing_webhook_secret: str | None = Field(
        default=None, alias="BILLING_WEBHOOK_SECRET"
    )

    @property
    def auth_configured(self) -> bool:
        return bool(self.clerk_jwks_url and self.clerk_issuer)

    @model_validator(mode="after")
    def _reject_insecure_defaults_in_production(self) -> "Settings":
        """Fail fast if production is left on the local development defaults."""
        if self.environment == "production":
            if self.database_url == INSECURE_DEFAULT_DATABASE_URL:
                raise ValueError(
                    "DATABASE_URL must be set explicitly in production; "
                    "the local development default is not permitted."
                )
            if not self.auth_configured:
                raise ValueError(
                    "CLERK_JWKS_URL and CLERK_ISSUER must be set in production "
                    "to enforce authentication."
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
