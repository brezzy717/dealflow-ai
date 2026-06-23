"""Dashboard APIs: home metrics, appointments, clients, tasks, reports.

All endpoints are tenant-scoped through ``get_broker_context`` (RLS + resolved
broker). They back the broker dashboard tabs (spec §7).
"""

from __future__ import annotations

import csv
import datetime
import io
from collections import Counter

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from sqlalchemy import func, select

from ..db import models
from .context import BrokerContext, get_broker_context

router = APIRouter(prefix="/api", tags=["dashboard"])

_CLIENT_STATUSES = (models.AssignmentStatus.client, models.AssignmentStatus.past_client)


@router.get("/metrics")
async def home_metrics(ctx: BrokerContext = Depends(get_broker_context)) -> dict:
    """Top-of-dashboard counters: prospects, appointments, conversions."""
    if ctx.user is None:
        return {"prospects": 0, "clients": 0, "appointments": 0, "closed_deals": 0}
    session, user = ctx.session, ctx.user

    async def count(stmt) -> int:
        return int((await session.execute(stmt)).scalar_one())

    prospects = await count(
        select(func.count())
        .select_from(models.LeadAssignment)
        .where(
            models.LeadAssignment.user_id == user.id,
            models.LeadAssignment.status == models.AssignmentStatus.prospect,
        )
    )
    clients = await count(
        select(func.count())
        .select_from(models.LeadAssignment)
        .where(
            models.LeadAssignment.user_id == user.id,
            models.LeadAssignment.status.in_(_CLIENT_STATUSES),
        )
    )
    appointments = await count(
        select(func.count())
        .select_from(models.Appointment)
        .where(models.Appointment.user_id == user.id)
    )
    closed = await count(
        select(func.count())
        .select_from(models.DealOutcome)
        .join(
            models.LeadAssignment,
            models.LeadAssignment.id == models.DealOutcome.assignment_id,
        )
        .where(
            models.LeadAssignment.user_id == user.id,
            models.DealOutcome.actual_outcome == "closed",
        )
    )
    appt_rate = round(appointments / prospects, 3) if prospects else 0.0
    close_rate = round(closed / appointments, 3) if appointments else 0.0
    return {
        "prospects": prospects,
        "clients": clients,
        "appointments": appointments,
        "closed_deals": closed,
        "prospect_to_appointment_rate": appt_rate,
        "appointment_to_close_rate": close_rate,
        # Commission tracking is a tracked gap (no commission data captured yet).
        "ytd_commissions": None,
    }


@router.get("/appointments")
async def list_appointments(ctx: BrokerContext = Depends(get_broker_context)) -> dict:
    if ctx.user is None:
        return {"appointments": []}
    rows = (
        await ctx.session.execute(
            select(models.Appointment)
            .where(models.Appointment.user_id == ctx.user.id)
            .order_by(models.Appointment.scheduled_at.asc())
        )
    ).scalars().all()
    return {
        "appointments": [
            {
                "id": str(a.id),
                "source": a.source,
                "scheduled_at": a.scheduled_at.isoformat(),
                "status": a.status,
            }
            for a in rows
        ]
    }


@router.get("/clients")
async def list_clients(ctx: BrokerContext = Depends(get_broker_context)) -> dict:
    if ctx.user is None:
        return {"clients": []}
    rows = (
        await ctx.session.execute(
            select(models.LeadAssignment, models.RawLead)
            .join(models.RawLead, models.RawLead.id == models.LeadAssignment.lead_id)
            .where(
                models.LeadAssignment.user_id == ctx.user.id,
                models.LeadAssignment.status.in_(_CLIENT_STATUSES),
            )
        )
    ).all()
    return {
        "clients": [
            {
                "assignment_id": str(a.id),
                "status": a.status.value,
                "business_name": lead.business_name,
                "industry": lead.industry,
                "owner_name": lead.owner_name,
            }
            for a, lead in rows
        ]
    }


class TaskIn(BaseModel):
    title: str
    description: str | None = None
    due_at: datetime.datetime | None = None


@router.get("/tasks")
async def list_tasks(ctx: BrokerContext = Depends(get_broker_context)) -> dict:
    if ctx.user is None:
        return {"tasks": []}
    rows = (
        await ctx.session.execute(
            select(models.Task)
            .where(models.Task.user_id == ctx.user.id)
            .order_by(models.Task.created_at.desc())
        )
    ).scalars().all()
    return {
        "tasks": [
            {
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "status": t.status.value,
                "due_at": t.due_at.isoformat() if t.due_at else None,
            }
            for t in rows
        ]
    }


@router.post("/tasks")
async def create_task(
    body: TaskIn, ctx: BrokerContext = Depends(get_broker_context)
) -> dict:
    if ctx.user is None:
        return {"created": False}
    task = models.Task(
        tenant_id=ctx.user.tenant_id,
        user_id=ctx.user.id,
        title=body.title,
        description=body.description,
        due_at=body.due_at,
    )
    ctx.session.add(task)
    await ctx.session.commit()
    return {"created": True, "id": str(task.id)}


@router.get("/reports/summary")
async def reports_summary(ctx: BrokerContext = Depends(get_broker_context)) -> dict:
    """Drill-down aggregates: tier mix, top industries, deal outcomes."""
    if ctx.user is None:
        return {"by_tier": {}, "top_industries": {}, "outcomes": {}}
    session, user = ctx.session, ctx.user

    tier_rows = (
        await session.execute(
            select(models.LeadAssignment.tier, func.count())
            .where(models.LeadAssignment.user_id == user.id)
            .group_by(models.LeadAssignment.tier)
        )
    ).all()
    by_tier = {tier.value: int(n) for tier, n in tier_rows}

    industry_rows = (
        await session.execute(
            select(models.RawLead.industry)
            .join(
                models.LeadAssignment,
                models.LeadAssignment.lead_id == models.RawLead.id,
            )
            .where(models.LeadAssignment.user_id == user.id)
        )
    ).scalars().all()
    top_industries = dict(Counter(i for i in industry_rows if i).most_common(5))

    outcome_rows = (
        await session.execute(
            select(models.DealOutcome.actual_outcome, func.count())
            .join(
                models.LeadAssignment,
                models.LeadAssignment.id == models.DealOutcome.assignment_id,
            )
            .where(models.LeadAssignment.user_id == user.id)
            .group_by(models.DealOutcome.actual_outcome)
        )
    ).all()
    outcomes = {outcome: int(n) for outcome, n in outcome_rows}

    return {"by_tier": by_tier, "top_industries": top_industries, "outcomes": outcomes}


_EXPORT_FIELDS = (
    "assignment_id",
    "status",
    "tier",
    "business_name",
    "industry",
    "city",
    "state",
    "owner_name",
    "owner_email",
    "owner_phone",
)


@router.get("/export/prospects")
async def export_prospects(
    ctx: BrokerContext = Depends(get_broker_context),
    fmt: str = Query(default="csv", pattern="^(csv|json)$", alias="format"),
) -> Response:
    """Export the broker's prospects/clients as CSV or JSON (spec §7 export)."""
    records: list[dict] = []
    if ctx.user is not None:
        rows = (
            await ctx.session.execute(
                select(models.LeadAssignment, models.RawLead)
                .join(
                    models.RawLead, models.RawLead.id == models.LeadAssignment.lead_id
                )
                .where(models.LeadAssignment.user_id == ctx.user.id)
            )
        ).all()
        for assignment, lead in rows:
            records.append(
                {
                    "assignment_id": str(assignment.id),
                    "status": assignment.status.value,
                    "tier": assignment.tier.value,
                    "business_name": lead.business_name,
                    "industry": lead.industry,
                    "city": lead.city,
                    "state": lead.state,
                    "owner_name": lead.owner_name,
                    "owner_email": lead.owner_email,
                    "owner_phone": lead.owner_phone,
                }
            )

    if fmt == "json":
        return JSONResponse(content={"prospects": records})

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_EXPORT_FIELDS)
    writer.writeheader()
    writer.writerows(records)
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=prospects.csv"},
    )
