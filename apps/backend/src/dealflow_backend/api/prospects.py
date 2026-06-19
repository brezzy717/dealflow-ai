"""Prospects API: a broker's assigned, scored leads (the Phase 2 slice surface)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_async_session, set_current_tenant
from ..db import models
from .dependencies import AuthenticatedUser, get_current_user

router = APIRouter(prefix="/api/prospects", tags=["prospects"])


@router.get("")
async def list_prospects(
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    if not user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token has no tenant.",
        )
    # Set the RLS tenant from the verified JWT before any tenant-scoped query.
    await set_current_tenant(session, user.tenant_id)

    internal_user = (
        await session.execute(
            select(models.User).where(models.User.clerk_user_id == user.user_id)
        )
    ).scalar_one_or_none()
    if internal_user is None:
        return {"prospects": []}

    rows = (
        await session.execute(
            select(models.LeadAssignment, models.RawLead)
            .join(models.RawLead, models.RawLead.id == models.LeadAssignment.lead_id)
            .where(models.LeadAssignment.user_id == internal_user.id)
            .order_by(models.LeadAssignment.assigned_at.desc())
        )
    ).all()

    lead_ids = [lead.id for _, lead in rows]
    latest_prediction: dict[uuid.UUID, models.EnsemblePrediction] = {}
    if lead_ids:
        predictions = (
            await session.execute(
                select(models.EnsemblePrediction)
                .where(models.EnsemblePrediction.lead_id.in_(lead_ids))
                .order_by(models.EnsemblePrediction.scored_at.desc())
            )
        ).scalars().all()
        for row_prediction in predictions:
            # First seen per lead is the latest (desc order).
            latest_prediction.setdefault(row_prediction.lead_id, row_prediction)

    prospects = []
    for assignment, lead in rows:
        prediction = latest_prediction.get(lead.id)
        prospects.append(
            {
                "assignment_id": str(assignment.id),
                "status": assignment.status.value,
                "tier": assignment.tier.value,
                "business_name": lead.business_name,
                "industry": lead.industry,
                "city": lead.city,
                "state": lead.state,
                "employee_count": lead.employee_count,
                "revenue_millions": float(lead.revenue_millions)
                if lead.revenue_millions is not None
                else None,
                "years_in_business": lead.years_in_business,
                "owner_name": lead.owner_name,
                "score": float(prediction.ensemble_score) if prediction else None,
                "confidence": float(prediction.confidence)
                if prediction and prediction.confidence is not None
                else None,
                "explanation": prediction.explanation if prediction else None,
                "top_positive": prediction.top_positive if prediction else [],
                "top_negative": prediction.top_negative if prediction else [],
            }
        )

    return {"prospects": prospects}
