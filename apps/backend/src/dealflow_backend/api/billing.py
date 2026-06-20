"""Billing (Stripe) — status + webhook (spec §8).

Subscription state is kept on the tenant's settings JSON. The webhook updates it
from billing events. Live Stripe signature verification + a real adapter are
tracked gaps; the webhook here verifies a shared secret header as a stand-in.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..core.db import get_async_session
from ..db import models
from .context import BrokerContext, get_broker_context

router = APIRouter(prefix="/api/billing", tags=["billing"])

_VALID_STATUSES = {"trialing", "active", "past_due", "canceled"}


@router.get("/status")
async def billing_status(ctx: BrokerContext = Depends(get_broker_context)) -> dict:
    if ctx.user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker.")
    tenant = (
        await ctx.session.execute(
            select(models.Tenant).where(models.Tenant.id == ctx.user.tenant_id)
        )
    ).scalar_one()
    settings = tenant.settings or {}
    return {
        "tenant_id": str(tenant.id),
        "subscription_status": settings.get("subscription_status", "trialing"),
    }


class BillingEvent(BaseModel):
    tenant_id: uuid.UUID
    subscription_status: str


@router.post("/webhook")
async def billing_webhook(
    event: BillingEvent,
    x_billing_secret: str | None = Header(default=None),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Update subscription state from a billing event (shared-secret verified)."""
    expected = get_settings().billing_webhook_secret
    if not expected or x_billing_secret != expected:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid billing signature.")
    if event.subscription_status not in _VALID_STATUSES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid status.")

    tenant = (
        await session.execute(
            select(models.Tenant).where(models.Tenant.id == event.tenant_id)
        )
    ).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found.")
    settings = dict(tenant.settings or {})
    settings["subscription_status"] = event.subscription_status
    tenant.settings = settings
    await session.commit()
    return {"updated": True, "subscription_status": event.subscription_status}
