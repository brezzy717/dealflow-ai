from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status

from ..auth import ClerkVerifierError, get_clerk_verifier
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
    """Identity resolved from a verified Clerk session token."""

    user_id: str
    tenant_id: str | None = None
    claims: dict | None = None


def _bearer_token(authorization: str | None) -> str:
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
    return token


async def get_current_user(
    authorization: str | None = Header(default=None),
) -> AuthenticatedUser:
    """Resolve and verify the caller from the Clerk session token.

    The tenant is taken from the Clerk organization claim (``org_id``); a custom
    ``tenant_id`` claim takes precedence when present.
    """
    token = _bearer_token(authorization)

    verifier = get_clerk_verifier()
    if verifier is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured.",
        )

    try:
        claims = verifier.verify(token)
    except ClerkVerifierError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing a subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    tenant_id = claims.get("tenant_id") or claims.get("org_id")
    return AuthenticatedUser(user_id=user_id, tenant_id=tenant_id, claims=claims)


async def require_admin(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Restrict a route to admin callers (Clerk ``role`` / ``org_role`` claim)."""
    claims = user.claims or {}
    role = claims.get("role") or claims.get("org_role")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required.",
        )
    return user
