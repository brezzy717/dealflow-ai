"""Feedback capture: call outcomes, deal outcomes, and admin retrain trigger.

These endpoints close the two-stage feedback loop (appointment booked -> deal
closed/lost). Deal outcomes record the prediction error that the retraining job
learns from (MASTER_BUILD_SPEC §3, §6).
"""

from __future__ import annotations

import datetime
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_async_session, set_current_tenant
from ..db import models
from .dependencies import AuthenticatedUser, get_current_user, require_admin

router = APIRouter(prefix="/api", tags=["feedback"])

# Outcomes that count as having made contact with the owner.
_CONTACT_OUTCOMES = {"booked", "dnc", "interested_future"}


class CallOutcomeIn(BaseModel):
    outcome: Literal["booked", "dnc", "interested_future", "no_contact"]
    reason: str | None = None
    callback_at: datetime.datetime | None = None


class DealOutcomeIn(BaseModel):
    outcome: Literal["closed", "lost"]
    quality_score: float | None = None
    loss_reason: str | None = None


async def _load_assignment(
    session: AsyncSession, assignment_id: uuid.UUID, user_clerk_id: str
) -> models.LeadAssignment:
    user = (
        await session.execute(
            select(models.User).where(models.User.clerk_user_id == user_clerk_id)
        )
    ).scalar_one_or_none()
    assignment = (
        await session.execute(
            select(models.LeadAssignment).where(
                models.LeadAssignment.id == assignment_id
            )
        )
    ).scalar_one_or_none()
    if user is None or assignment is None or assignment.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prospect not found."
        )
    return assignment


@router.post("/prospects/{assignment_id}/call-outcome")
async def record_call_outcome(
    assignment_id: uuid.UUID,
    body: CallOutcomeIn,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    if not user.tenant_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Token has no tenant.")
    await set_current_tenant(session, user.tenant_id)
    assignment = await _load_assignment(session, assignment_id, user.user_id)

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    attempts = (
        await session.execute(
            select(func.count())
            .select_from(models.AiCallOutcome)
            .where(models.AiCallOutcome.assignment_id == assignment_id)
        )
    ).scalar_one()

    session.add(
        models.AiCallOutcome(
            tenant_id=assignment.tenant_id,
            assignment_id=assignment_id,
            attempt_no=int(attempts) + 1,
            outcome=models.CallOutcome(body.outcome),
            reason=body.reason,
            callback_at=body.callback_at,
            actor="broker",
            occurred_at=now,
        )
    )
    if body.outcome in _CONTACT_OUTCOMES and assignment.first_contact_at is None:
        assignment.first_contact_at = now

    await session.commit()
    return {"status": "recorded", "outcome": body.outcome, "attempt_no": int(attempts) + 1}


@router.post("/prospects/{assignment_id}/deal-outcome")
async def record_deal_outcome(
    assignment_id: uuid.UUID,
    body: DealOutcomeIn,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    if not user.tenant_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Token has no tenant.")
    await set_current_tenant(session, user.tenant_id)
    assignment = await _load_assignment(session, assignment_id, user.user_id)

    prediction = (
        await session.execute(
            select(models.EnsemblePrediction)
            .where(models.EnsemblePrediction.lead_id == assignment.lead_id)
            .order_by(models.EnsemblePrediction.scored_at.desc())
        )
    ).scalars().first()
    predicted = float(prediction.ensemble_score) if prediction else None

    # If the broker didn't grade quality, infer from the binary outcome.
    actual_quality = body.quality_score
    if actual_quality is None:
        actual_quality = 100.0 if body.outcome == "closed" else 0.0
    prediction_error = abs(predicted - actual_quality) if predicted is not None else None

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    session.add(
        models.DealOutcome(
            tenant_id=assignment.tenant_id,
            assignment_id=assignment_id,
            predicted_score=predicted,
            actual_outcome=body.outcome,
            actual_quality_score=actual_quality,
            prediction_error=prediction_error,
            loss_reason=body.loss_reason,
            occurred_at=now,
        )
    )
    if body.outcome == "closed":
        assignment.status = models.AssignmentStatus.client

    await session.commit()
    return {
        "status": "recorded",
        "outcome": body.outcome,
        "predicted_score": predicted,
        "actual_quality_score": actual_quality,
        "prediction_error": prediction_error,
    }


@router.post("/admin/retrain")
async def trigger_retrain(
    _: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    from ..config import get_settings
    from ..services.retraining import retrain_from_feedback

    return await retrain_from_feedback(
        session, artifacts_dir=get_settings().model_artifacts_dir
    )


@router.post("/admin/jobs/{job_name}")
async def trigger_job(
    job_name: str,
    _: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Trigger a scheduled job (refresh / assign / retrain) — called by cron."""
    from ..services.scheduling import JOBS, run_job

    if job_name not in JOBS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown job '{job_name}'. Valid: {sorted(JOBS)}",
        )
    return await run_job(job_name, session)
