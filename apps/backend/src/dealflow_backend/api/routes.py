from fastapi import APIRouter


router = APIRouter()


@router.get("/health", tags=["health"])  # pragma: no cover - simple ping endpoint
async def health_check() -> dict[str, str]:
    """Basic health probe used by CI and orchestration layers."""
    return {"status": "ok"}
