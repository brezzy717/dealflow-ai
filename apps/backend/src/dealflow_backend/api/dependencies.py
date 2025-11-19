from fastapi import Depends

from ..config import Settings, get_settings
from ..services.lead_service import LeadService


def get_app_settings() -> Settings:
    """Expose application settings to FastAPI."""
    return get_settings()


def get_lead_service(settings: Settings = Depends(get_app_settings)) -> LeadService:
    """Provide the lead service with injected configuration."""
    return LeadService(settings=settings)
