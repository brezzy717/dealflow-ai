import datetime

from dealflow_backend.services.outreach.providers import (
    ConsoleEmailProvider,
    NoOpVoiceProvider,
    StaticBookingProvider,
)
from dealflow_backend.services.outreach.state_machine import plan_next_step

NOW = datetime.datetime(2026, 6, 20, tzinfo=datetime.timezone.utc)


def test_booked_is_done() -> None:
    plan = plan_next_step(outcome="booked", attempt_no=1, now=NOW)
    assert plan.action == "done"
    assert plan.callback_at is None


def test_dnc_deactivates() -> None:
    assert plan_next_step(outcome="dnc", attempt_no=1, now=NOW).action == "deactivate"


def test_no_contact_first_then_second() -> None:
    first = plan_next_step(outcome="no_contact", attempt_no=1, now=NOW)
    assert first.action == "callback"
    assert (first.callback_at - NOW).days == 3
    second = plan_next_step(outcome="no_contact", attempt_no=2, now=NOW)
    assert (second.callback_at - NOW).days == 60


def test_interested_future_uses_timeframe_or_default() -> None:
    default = plan_next_step(outcome="interested_future", attempt_no=1, now=NOW)
    assert (default.callback_at - NOW).days == 60
    custom = plan_next_step(
        outcome="interested_future", attempt_no=1, now=NOW, callback_timeframe_days=14
    )
    assert (custom.callback_at - NOW).days == 14


def test_providers_have_safe_noop_defaults() -> None:
    msg = ConsoleEmailProvider().send(to="a@b.com", subject="hi", body="x")
    assert msg.startswith("console:")
    link = StaticBookingProvider(base_url="https://cal.test").booking_link(
        broker_handle="jane"
    )
    assert link == "https://cal.test/jane/discovery-call"
    assert NoOpVoiceProvider().place_call(to="555", script="s").outcome == "no_contact"
