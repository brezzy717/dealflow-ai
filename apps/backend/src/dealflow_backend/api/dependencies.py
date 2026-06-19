from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status

from ..config import Settings, get_settings
from ..services.lead_service import LeadService


def get_app_settings() -> Settings:
    """Expose application settings to FastAPI."""
    return get_settings()


def get_lead_service(settings: Settings = Depends(get_app_settings)) -> LeadService:
    """Provide the lead service with injected configuration."""
    return LeadService(settings=settings)


@dataclass(frozen=True)
class AuthenticatedUser:
    """Identity resolved from the incoming request's bearer token."""

    user_id: str
    tenant_id: str | None = None


async def get_current_user(
    authorization: str | None = Header(default=None),
) -> AuthenticatedUser:
    """Placeholder auth dependency.

    Phase 1 replaces this body with Clerk JWT verification (signature, issuer,
    and expiry checks) that resolves the user and tenant. It already rejects
    missing/malformed credentials so protected routes can depend on it today.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # NOTE: token is not yet cryptographically verified — see docstring.
    return AuthenticatedUser(user_id="pending-clerk-integration")
