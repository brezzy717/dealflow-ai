from fastapi import APIRouter, Depends

from .dependencies import AuthenticatedUser, get_current_user

router = APIRouter()


@router.get("/health", tags=["health"])  # pragma: no cover - simple ping endpoint
async def health_check() -> dict[str, str]:
    """Basic health probe used by CI and orchestration layers."""
    return {"status": "ok"}


api_router = APIRouter(prefix="/api", tags=["api"])


@api_router.get("/me")
async def whoami(
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, str | None]:
    """Return the authenticated caller; exercises Clerk verification + tenancy."""
    return {"user_id": user.user_id, "tenant_id": user.tenant_id}
