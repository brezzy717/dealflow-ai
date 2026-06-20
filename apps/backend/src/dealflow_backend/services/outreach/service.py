"""Outreach orchestration over the database.

Day 0: an email with value PDFs + a booking link goes out the moment a prospect
lands, and a Day-7 call is queued. The concierge then works the call queue,
skipping anyone who already booked or replied, recording outcomes, and scheduling
the next step from the state machine. Automated calling only runs for brokers who
opted into warm outreach; opted-out brokers log outcomes manually (spec §6).
"""

from __future__ import annotations

import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import models
from .providers import (
    BookingProvider,
    EmailProvider,
    VoiceProvider,
    get_booking_provider,
    get_email_provider,
    get_voice_provider,
)
from .state_machine import plan_next_step

CALL_WINDOW_HOURS = 2
FIRST_CALL_DELAY_DAYS = 7
VALUE_PDFS = ["seller-checklist.pdf", "maximize-valuation.pdf"]
_CONTACT_OUTCOMES = {"booked", "interested_future", "dnc"}


def _broker_handle(user: models.User) -> str:
    return (user.email or str(user.id)).split("@")[0]


def _email_body(booking_link: str) -> str:
    return (
        "We work with owners exploring a sale and would love to offer a free, "
        "no-obligation valuation on a 30-minute discovery call. Book any time: "
        f"{booking_link}\n\nTwo quick guides are attached to help you prepare."
    )


async def start_outreach_for_new_assignments(
    session: AsyncSession,
    *,
    now: datetime.datetime | None = None,
    email_provider: EmailProvider | None = None,
    booking_provider: BookingProvider | None = None,
    tenant_id=None,
) -> dict:
    """Send Day-0 emails and queue Day-7 calls for assignments with no outreach."""
    now = now or datetime.datetime.now(tz=datetime.timezone.utc)
    email_provider = email_provider or get_email_provider()
    booking_provider = booking_provider or get_booking_provider()

    already = select(models.LeadEmailOutreach.assignment_id)
    query = (
        select(models.LeadAssignment, models.RawLead, models.User)
        .join(models.RawLead, models.RawLead.id == models.LeadAssignment.lead_id)
        .join(models.User, models.User.id == models.LeadAssignment.user_id)
        .where(models.LeadAssignment.id.notin_(already))
    )
    if tenant_id is not None:
        query = query.where(models.LeadAssignment.tenant_id == tenant_id)
    rows = (await session.execute(query)).all()

    emails_sent = 0
    calls_queued = 0
    for assignment, lead, user in rows:
        link = booking_provider.booking_link(broker_handle=_broker_handle(user))
        if lead.owner_email:
            email_provider.send(
                to=lead.owner_email,
                subject="A free valuation for your business",
                body=_email_body(link),
                attachments=VALUE_PDFS,
            )
            emails_sent += 1
        session.add(
            models.LeadEmailOutreach(
                tenant_id=assignment.tenant_id,
                assignment_id=assignment.id,
                template="day0",
                sent_at=now,
            )
        )
        window_start = now + datetime.timedelta(days=FIRST_CALL_DELAY_DAYS)
        session.add(
            models.AiCallQueue(
                tenant_id=assignment.tenant_id,
                assignment_id=assignment.id,
                window_start=window_start,
                window_end=window_start + datetime.timedelta(hours=CALL_WINDOW_HOURS),
                attempt_no=1,
                status="scheduled",
            )
        )
        calls_queued += 1

    await session.commit()
    return {"emails_sent": emails_sent, "calls_queued": calls_queued}


async def _is_engaged(session: AsyncSession, assignment_id) -> bool:
    appt = (
        await session.execute(
            select(models.Appointment.id).where(
                models.Appointment.assignment_id == assignment_id
            )
        )
    ).first()
    if appt is not None:
        return True
    replied = (
        await session.execute(
            select(models.LeadEmailOutreach.id).where(
                models.LeadEmailOutreach.assignment_id == assignment_id,
                models.LeadEmailOutreach.replied_at.is_not(None),
            )
        )
    ).first()
    return replied is not None


async def run_concierge(
    session: AsyncSession,
    *,
    now: datetime.datetime | None = None,
    voice_provider: VoiceProvider | None = None,
    tenant_id=None,
) -> dict:
    """Work the due call queue for opted-in brokers; record outcomes + callbacks."""
    now = now or datetime.datetime.now(tz=datetime.timezone.utc)
    voice_provider = voice_provider or get_voice_provider()

    query = (
        select(models.AiCallQueue, models.LeadAssignment, models.RawLead, models.User)
        .join(
            models.LeadAssignment,
            models.LeadAssignment.id == models.AiCallQueue.assignment_id,
        )
        .join(models.RawLead, models.RawLead.id == models.LeadAssignment.lead_id)
        .join(models.User, models.User.id == models.LeadAssignment.user_id)
        .where(
            models.AiCallQueue.status == "scheduled",
            models.AiCallQueue.window_start <= now,
        )
    )
    if tenant_id is not None:
        query = query.where(models.AiCallQueue.tenant_id == tenant_id)
    due = (await session.execute(query)).all()

    placed = 0
    skipped = 0
    for queue_entry, assignment, lead, user in due:
        if not user.warm_outreach_opt_in:
            queue_entry.status = "manual"  # broker handles outreach themselves
            skipped += 1
            continue
        if await _is_engaged(session, assignment.id):
            queue_entry.status = "cancelled_engaged"
            skipped += 1
            continue

        result = voice_provider.place_call(
            to=lead.owner_phone or "", script="discovery-call-invite"
        )
        session.add(
            models.AiCallOutcome(
                tenant_id=assignment.tenant_id,
                assignment_id=assignment.id,
                attempt_no=queue_entry.attempt_no,
                outcome=models.CallOutcome(result.outcome),
                recording_uri=result.recording_uri,
                transcript_uri=result.transcript_uri,
                actor="concierge",
                occurred_at=now,
            )
        )
        if result.outcome in _CONTACT_OUTCOMES and assignment.first_contact_at is None:
            assignment.first_contact_at = now
        if result.outcome == "booked":
            session.add(
                models.Appointment(
                    tenant_id=assignment.tenant_id,
                    assignment_id=assignment.id,
                    user_id=user.id,
                    source="ai_concierge",
                    scheduled_at=now + datetime.timedelta(days=1),
                    status="booked",
                )
            )
        queue_entry.status = "completed"

        plan = plan_next_step(
            outcome=result.outcome,
            attempt_no=queue_entry.attempt_no,
            now=now,
            callback_timeframe_days=result.callback_timeframe_days,
        )
        if plan.action == "callback" and plan.callback_at is not None:
            session.add(
                models.AiCallQueue(
                    tenant_id=assignment.tenant_id,
                    assignment_id=assignment.id,
                    window_start=plan.callback_at,
                    window_end=plan.callback_at
                    + datetime.timedelta(hours=CALL_WINDOW_HOURS),
                    attempt_no=queue_entry.attempt_no + 1,
                    status="scheduled",
                )
            )
        placed += 1

    await session.commit()
    return {"calls_placed": placed, "skipped": skipped}
