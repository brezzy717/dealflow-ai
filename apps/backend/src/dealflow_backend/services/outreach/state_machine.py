"""Outreach outcome -> next-step state machine (spec §6).

Encodes the call cadence and callback rules:
- ``booked``            -> done (discovery call is on the calendar)
- ``dnc``               -> deactivate (remove from the calling list)
- ``interested_future`` -> callback at the requested timeframe (default +60 days)
- ``no_contact`` (1st)  -> retry in 3 days (the Day-7 -> Day-10 second call)
- ``no_contact`` (2nd+) -> re-sequence in 60 days
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

SECOND_CALL_GAP_DAYS = 3
RESEQUENCE_DAYS = 60
DEFAULT_INTERESTED_CALLBACK_DAYS = 60


@dataclass
class CallbackPlan:
    action: str  # "done" | "deactivate" | "callback"
    callback_at: datetime.datetime | None
    reason: str


def plan_next_step(
    *,
    outcome: str,
    attempt_no: int,
    now: datetime.datetime,
    callback_timeframe_days: int | None = None,
) -> CallbackPlan:
    if outcome == "booked":
        return CallbackPlan("done", None, "appointment booked")
    if outcome == "dnc":
        return CallbackPlan("deactivate", None, "do-not-contact requested")
    if outcome == "interested_future":
        days = callback_timeframe_days or DEFAULT_INTERESTED_CALLBACK_DAYS
        return CallbackPlan(
            "callback",
            now + datetime.timedelta(days=days),
            f"interested, follow up in {days} days",
        )
    if outcome == "no_contact":
        if attempt_no <= 1:
            return CallbackPlan(
                "callback",
                now + datetime.timedelta(days=SECOND_CALL_GAP_DAYS),
                "no contact, second call in 3 days",
            )
        return CallbackPlan(
            "callback",
            now + datetime.timedelta(days=RESEQUENCE_DAYS),
            "no contact, re-sequence in 60 days",
        )
    raise ValueError(f"Unknown outcome: {outcome}")
