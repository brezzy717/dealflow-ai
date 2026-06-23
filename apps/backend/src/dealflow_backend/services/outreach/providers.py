"""Outreach provider interfaces with no-op defaults.

The platform talks to email (Resend/SendGrid), booking (self-hosted Cal.com), and
voice (Hume AI + Twilio, Re-tell fallback) through these interfaces. No-op
implementations let the full orchestration run without third-party credentials;
real adapters are selected by config once keys are present (coverage ledger rows
4.1-4.4). Provider wiring to live services is the remaining gap.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)


# --- Email ------------------------------------------------------------------


class EmailProvider(Protocol):
    def send(
        self, *, to: str, subject: str, body: str, attachments: list[str] | None = None
    ) -> str:
        """Send an email; return a provider message id."""
        ...


class ConsoleEmailProvider:
    """Logs instead of sending. Default until an email API key is configured."""

    def send(
        self, *, to: str, subject: str, body: str, attachments: list[str] | None = None
    ) -> str:
        logger.info("outreach_email", extra={"to": to, "subject": subject})
        return f"console:{to}:{subject}"


# --- Booking (Cal.com) ------------------------------------------------------


class BookingProvider(Protocol):
    def booking_link(self, *, broker_handle: str) -> str:
        ...


@dataclass
class StaticBookingProvider:
    """Builds a Cal.com-style booking URL from a base + broker handle."""

    base_url: str = "https://cal.example.com"

    def booking_link(self, *, broker_handle: str) -> str:
        return f"{self.base_url.rstrip('/')}/{broker_handle}/discovery-call"


# --- Voice (Hume / Twilio) --------------------------------------------------


@dataclass
class CallResult:
    outcome: str  # booked | no_contact | interested_future | dnc
    recording_uri: str | None = None
    transcript_uri: str | None = None
    callback_timeframe_days: int | None = None


class VoiceProvider(Protocol):
    def place_call(self, *, to: str, script: str) -> CallResult:
        ...


class NoOpVoiceProvider:
    """Returns 'no_contact' without dialing. Default until voice is configured."""

    def place_call(self, *, to: str, script: str) -> CallResult:
        logger.info("outreach_call", extra={"to": to})
        return CallResult(outcome="no_contact")


# --- Config-driven factories ------------------------------------------------


def get_email_provider() -> EmailProvider:
    # A real adapter (Resend/SendGrid) is selected here when configured.
    return ConsoleEmailProvider()


def get_booking_provider() -> BookingProvider:
    return StaticBookingProvider()


def get_voice_provider() -> VoiceProvider:
    return NoOpVoiceProvider()
