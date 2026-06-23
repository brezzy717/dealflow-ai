"""Shared broker request context: tenant RLS + resolved internal user."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_async_session, set_current_tenant
from ..db import models
from .dependencies import AuthenticatedUser, get_current_user


@dataclass
class BrokerContext:
    session: AsyncSession
    user: models.User | None


async def get_broker_context(
    auth: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> BrokerContext:
    """Set the RLS tenant from the JWT and resolve the internal broker user."""
    if not auth.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Token has no tenant."
        )
    await set_current_tenant(session, auth.tenant_id)
    user = (
        await session.execute(
            select(models.User).where(models.User.clerk_user_id == auth.user_id)
        )
    ).scalar_one_or_none()
    return BrokerContext(session=session, user=user)
