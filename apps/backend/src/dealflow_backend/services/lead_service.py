"""Lead domain service.

This is an intentionally small starting point for the lead/prospect domain.
It exists so the dependency-injection wiring in ``api/dependencies.py`` is
importable and the service boundary is established; richer behavior (scoring
hand-off, assignment, outreach triggers) is layered on in later phases.
"""

from __future__ import annotations

from ..config import Settings


class LeadService:
    """Coordinates lead/prospect operations for API handlers."""

    def __init__(self, *, settings: Settings) -> None:
        self._settings = settings

    @property
    def settings(self) -> Settings:
        return self._settings
