"""Outreach automation: email, booking, AI calling concierge."""

from .providers import (
    BookingProvider,
    CallResult,
    ConsoleEmailProvider,
    EmailProvider,
    NoOpVoiceProvider,
    StaticBookingProvider,
    VoiceProvider,
    get_booking_provider,
    get_email_provider,
    get_voice_provider,
)
from .state_machine import CallbackPlan, plan_next_step

__all__ = [
    "EmailProvider",
    "ConsoleEmailProvider",
    "BookingProvider",
    "StaticBookingProvider",
    "VoiceProvider",
    "NoOpVoiceProvider",
    "CallResult",
    "get_email_provider",
    "get_booking_provider",
    "get_voice_provider",
    "CallbackPlan",
    "plan_next_step",
]
