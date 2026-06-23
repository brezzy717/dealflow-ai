"""Onboarding + Settings: assignment parameters, outreach opt-in, account close.

Brokers set lead-assignment parameters and the warm-outreach toggle at onboarding
and edit them any time (spec §5, §7). Account close triggers purge-on-exit.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from ..db import models
from .context import BrokerContext, get_broker_context

router = APIRouter(prefix="/api", tags=["settings"])


class BrokerSettingsIn(BaseModel):
    min_years_in_business: int | None = None
    min_employees: int | None = None
    max_employees: int | None = None
    min_revenue_millions: float | None = None
    max_revenue_millions: float | None = None
    omitted_industries: list[str] = []
    omitted_locations: list[str] = []
    warm_outreach_opt_in: bool | None = None


async def _get_params(ctx: BrokerContext) -> models.BrokerParameters | None:
    assert ctx.user is not None
    return (
        await ctx.session.execute(
            select(models.BrokerParameters).where(
                models.BrokerParameters.user_id == ctx.user.id
            )
        )
    ).scalar_one_or_none()


async def _apply(ctx: BrokerContext, body: BrokerSettingsIn) -> models.BrokerParameters:
    assert ctx.user is not None
    params = await _get_params(ctx)
    if params is None:
        params = models.BrokerParameters(
            tenant_id=ctx.user.tenant_id, user_id=ctx.user.id
        )
        ctx.session.add(params)
    params.min_years_in_business = body.min_years_in_business
    params.min_employees = body.min_employees
    params.max_employees = body.max_employees
    params.min_revenue_millions = body.min_revenue_millions
    params.max_revenue_millions = body.max_revenue_millions
    params.omitted_industries = body.omitted_industries
    params.omitted_locations = body.omitted_locations
    if body.warm_outreach_opt_in is not None:
        ctx.user.warm_outreach_opt_in = body.warm_outreach_opt_in
    await ctx.session.commit()
    return params


def _serialize(
    user: models.User, params: models.BrokerParameters | None
) -> dict:
    return {
        "warm_outreach_opt_in": user.warm_outreach_opt_in,
        "parameters": {
            "min_years_in_business": params.min_years_in_business if params else None,
            "min_employees": params.min_employees if params else None,
            "max_employees": params.max_employees if params else None,
            "min_revenue_millions": float(params.min_revenue_millions)
            if params and params.min_revenue_millions is not None
            else None,
            "max_revenue_millions": float(params.max_revenue_millions)
            if params and params.max_revenue_millions is not None
            else None,
            "omitted_industries": params.omitted_industries if params else [],
            "omitted_locations": params.omitted_locations if params else [],
        },
    }


@router.get("/settings")
async def get_settings_view(ctx: BrokerContext = Depends(get_broker_context)) -> dict:
    if ctx.user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker.")
    return _serialize(ctx.user, await _get_params(ctx))


@router.put("/settings")
async def update_settings(
    body: BrokerSettingsIn, ctx: BrokerContext = Depends(get_broker_context)
) -> dict:
    if ctx.user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker.")
    return _serialize(ctx.user, await _apply(ctx, body))


@router.post("/onboarding")
async def onboarding(
    body: BrokerSettingsIn, ctx: BrokerContext = Depends(get_broker_context)
) -> dict:
    """Set initial assignment parameters + outreach preference."""
    if ctx.user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker.")
    return _serialize(ctx.user, await _apply(ctx, body))


@router.post("/account/close")
async def close_account(ctx: BrokerContext = Depends(get_broker_context)) -> dict:
    """Purge the broker's tenant (retains anonymized training data)."""
    if ctx.user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker.")
    from ..services.account import purge_tenant

    tenant_id: uuid.UUID = ctx.user.tenant_id
    return await purge_tenant(ctx.session, tenant_id=tenant_id)
