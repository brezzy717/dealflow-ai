"""Scheduling: cadence, action-gating, weekly assignment, and job dispatch.

Encodes the spec cadence (§4/§5): ingest+score Mon/Wed/Fri 10:00, assignment
Tue 06:00. A broker only receives the next drop once their outstanding prospects
are actioned (action-gating, coverage ledger rows 3.6-3.7). The cron schedules
are triggered externally (Vercel Cron / Cloud Scheduler) hitting the admin job
endpoint; this module is the in-process job logic.
"""

from __future__ import annotations

import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import models
from .assignment import Candidate
from .pipeline import assign_to_user, ingest_and_score

# Cron expressions (UTC). Triggered by an external scheduler.
CADENCE: dict[str, str] = {
    "refresh": "0 10 * * 1,3,5",  # Mon/Wed/Fri 10:00 — ingest + rescore
    "assign": "0 6 * * 2",        # Tue 06:00 — weekly lead drop
    "outreach": "0 12 * * 2,5",   # Tue/Fri 12:00 — Day-0 emails + concierge calls
    "retrain": "0 3 * * 1",       # Mon 03:00 — feedback retrain
}

GRACE_DAYS = 7


def is_eligible_for_drop(outstanding_unactioned: int) -> bool:
    """A broker receives the next drop only with zero overdue unactioned prospects."""
    return outstanding_unactioned == 0


async def count_outstanding_prospects(
    session: AsyncSession,
    *,
    user_id,
    now: datetime.datetime,
    grace_days: int = GRACE_DAYS,
) -> int:
    """Prospects past the grace window with no logged call or deal outcome."""
    cutoff = now - datetime.timedelta(days=grace_days)
    query = (
        select(func.count())
        .select_from(models.LeadAssignment)
        .where(
            models.LeadAssignment.user_id == user_id,
            models.LeadAssignment.status == models.AssignmentStatus.prospect,
            models.LeadAssignment.assigned_at < cutoff,
            models.LeadAssignment.id.notin_(select(models.AiCallOutcome.assignment_id)),
            models.LeadAssignment.id.notin_(select(models.DealOutcome.assignment_id)),
        )
    )
    return int((await session.execute(query)).scalar_one())


async def _pool_candidates(session: AsyncSession) -> list[Candidate]:
    """Unassigned, scored leads available for the next drop."""
    assigned = set(
        (await session.execute(select(models.LeadAssignment.lead_id))).scalars().all()
    )
    leads = (await session.execute(select(models.RawLead))).scalars().all()
    candidates: list[Candidate] = []
    for lead in leads:
        if lead.id in assigned:
            continue
        prediction = (
            await session.execute(
                select(models.EnsemblePrediction)
                .where(models.EnsemblePrediction.lead_id == lead.id)
                .order_by(models.EnsemblePrediction.scored_at.desc())
            )
        ).scalars().first()
        if prediction is None:
            continue
        candidates.append(
            Candidate(
                lead_id=str(lead.id),
                tier=prediction.tier.value,
                industry=lead.industry,
                employee_count=lead.employee_count,
                revenue_millions=float(lead.revenue_millions or 0),
                years_in_business=lead.years_in_business,
                location=lead.state,
            )
        )
    return candidates


async def assign_weekly(
    session: AsyncSession,
    *,
    now: datetime.datetime | None = None,
    grace_days: int = GRACE_DAYS,
    user_ids: set | None = None,
) -> dict:
    """Action-gated weekly drop to eligible active brokers.

    ``user_ids`` optionally restricts the run to specific brokers (the scheduled
    job runs all of them; targeting a subset is useful for re-runs and tests).
    """
    now = now or datetime.datetime.now(tz=datetime.timezone.utc)
    candidates = await _pool_candidates(session)
    user_query = select(models.User).where(models.User.is_active.is_(True))
    if user_ids is not None:
        user_query = user_query.where(models.User.id.in_(user_ids))
    users = (await session.execute(user_query)).scalars().all()

    results: dict[str, dict] = {}
    for user in users:
        outstanding = await count_outstanding_prospects(
            session, user_id=user.id, now=now, grace_days=grace_days
        )
        if not is_eligible_for_drop(outstanding):
            results[str(user.id)] = {"assigned": 0, "skipped_outstanding": outstanding}
            continue
        # autoflush makes prior brokers' new assignments visible to this call,
        # so no lead is double-assigned across the loop.
        assigned = await assign_to_user(
            session,
            tenant_id=user.tenant_id,
            user_id=user.id,
            candidates=candidates,
            now=now,
        )
        results[str(user.id)] = {"assigned": assigned}

    await session.commit()
    return results


async def _job_refresh(session: AsyncSession) -> dict:
    candidates, created = await ingest_and_score(session)
    await session.commit()
    return {"job": "refresh", "leads_created": created, "scored": len(candidates)}


async def _job_assign(session: AsyncSession) -> dict:
    return {"job": "assign", "brokers": await assign_weekly(session)}


async def _job_outreach(session: AsyncSession) -> dict:
    from .outreach.service import run_concierge, start_outreach_for_new_assignments

    emails = await start_outreach_for_new_assignments(session)
    calls = await run_concierge(session)
    return {"job": "outreach", **emails, **calls}


async def _job_retrain(session: AsyncSession) -> dict:
    from ..config import get_settings
    from .retraining import retrain_from_feedback

    result = await retrain_from_feedback(
        session, artifacts_dir=get_settings().model_artifacts_dir
    )
    return {"job": "retrain", **result}


JOBS = {
    "refresh": _job_refresh,
    "assign": _job_assign,
    "outreach": _job_outreach,
    "retrain": _job_retrain,
}


async def run_job(name: str, session: AsyncSession) -> dict:
    if name not in JOBS:
        raise KeyError(name)
    return await JOBS[name](session)
