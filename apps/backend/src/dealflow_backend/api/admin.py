"""Admin APIs: monitoring, error feed, model/drift, users, clawback (spec §7).

Admin endpoints are cross-tenant system views gated by ``require_admin``. In
production they run with a BYPASSRLS role (they do not set the tenant GUC); in CI
the superuser connection bypasses RLS. Real-time monitoring + admin UI auth are
tracked gaps.
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_async_session
from ..db import models
from .dependencies import AuthenticatedUser, require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def _count(session: AsyncSession, model) -> int:
    return int((await session.execute(select(func.count()).select_from(model))).scalar_one())


@router.get("/health")
async def platform_health(
    _: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Module monitoring: row counts + unacknowledged error count."""
    unacked = int(
        (
            await session.execute(
                select(func.count())
                .select_from(models.AdminNotification)
                .where(models.AdminNotification.acknowledged.is_(False))
            )
        ).scalar_one()
    )
    return {
        "tenants": await _count(session, models.Tenant),
        "users": await _count(session, models.User),
        "raw_leads": await _count(session, models.RawLead),
        "predictions": await _count(session, models.EnsemblePrediction),
        "assignments": await _count(session, models.LeadAssignment),
        "queued_calls": await _count(session, models.AiCallQueue),
        "unacknowledged_alerts": unacked,
    }


@router.get("/notifications")
async def list_notifications(
    _: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    rows = (
        await session.execute(
            select(models.AdminNotification)
            .order_by(models.AdminNotification.created_at.desc())
            .limit(100)
        )
    ).scalars().all()
    return {
        "notifications": [
            {
                "id": str(n.id),
                "level": n.level,
                "source": n.source,
                "message": n.message,
                "acknowledged": n.acknowledged,
                "created_at": n.created_at.isoformat(),
            }
            for n in rows
        ]
    }


@router.get("/models")
async def list_models(
    _: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Model registry + metrics for the drift dashboard."""
    rows = (
        await session.execute(
            select(models.ModelVersion).order_by(models.ModelVersion.created_at.desc())
        )
    ).scalars().all()
    return {
        "models": [
            {
                "id": str(m.id),
                "model_name": m.model_name,
                "version": m.version,
                "is_active": m.is_active,
                "metrics": m.metrics,
                "trained_at": m.trained_at.isoformat() if m.trained_at else None,
            }
            for m in rows
        ]
    }


@router.get("/users")
async def list_users(
    _: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    rows = (await session.execute(select(models.User))).scalars().all()
    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "role": u.role,
                "tenant_id": str(u.tenant_id),
                "is_active": u.is_active,
                "warm_outreach_opt_in": u.warm_outreach_opt_in,
            }
            for u in rows
        ]
    }


@router.get("/audit")
async def list_audit(
    _: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    rows = (
        await session.execute(
            select(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(100)
        )
    ).scalars().all()
    return {
        "audit": [
            {
                "id": str(a.id),
                "action": a.action,
                "target_type": a.target_type,
                "target_id": str(a.target_id) if a.target_id else None,
                "context": a.context,
                "created_at": a.created_at.isoformat(),
            }
            for a in rows
        ]
    }


@router.post("/clawback/{assignment_id}")
async def clawback_lead(
    assignment_id: uuid.UUID,
    admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Override a misassignment: remove the assignment so the lead re-pools."""
    assignment = (
        await session.execute(
            select(models.LeadAssignment).where(models.LeadAssignment.id == assignment_id)
        )
    ).scalar_one_or_none()
    if assignment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found.")

    lead_id = assignment.lead_id
    prior_user_id = assignment.user_id
    tenant_id = assignment.tenant_id

    await session.execute(
        delete(models.LeadAssignment).where(models.LeadAssignment.id == assignment_id)
    )
    session.add(
        models.AuditLog(
            tenant_id=tenant_id,
            action="lead_clawback",
            target_type="lead_assignment",
            target_id=assignment_id,
            context={
                "lead_id": str(lead_id),
                "prior_user_id": str(prior_user_id),
                "admin": admin.user_id,
                "at": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            },
        )
    )
    await session.commit()
    return {"clawed_back": True, "lead_id": str(lead_id)}
