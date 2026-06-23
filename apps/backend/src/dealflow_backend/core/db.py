from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..config import Settings, get_settings

# Postgres session variable read by the Row-Level Security policies.
TENANT_GUC = "app.current_tenant"


async def set_current_tenant(session: AsyncSession, tenant_id: uuid.UUID | str) -> None:
    """Bind the active tenant for the current transaction so RLS can enforce it.

    Uses ``set_config(..., is_local => true)`` so the setting is scoped to the
    transaction and cannot leak across pooled connections.
    """
    await session.execute(
        text("SELECT set_config(:key, :value, true)"),
        {"key": TENANT_GUC, "value": str(tenant_id)},
    )

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine(*, settings: Settings | None = None, force_new: bool = False) -> AsyncEngine:
    """Return the global async engine, creating it on first use."""
    global _engine

    if _engine is None or force_new:
        config = settings or get_settings()
        _engine = create_async_engine(
            config.database_url,
            echo=config.sqlalchemy_echo,
            future=True,
        )
    return _engine


def get_sessionmaker(*, settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    """Return an async session factory bound to the global engine."""
    global _session_factory

    if _session_factory is None:
        engine = get_engine(settings=settings)
        _session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return _session_factory


async def get_async_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields an async session."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        yield session


@asynccontextmanager
async def session_scope(*, settings: Settings | None = None) -> AsyncIterator[AsyncSession]:
    """Provide a transactional scope around a series of operations."""
    sessionmaker = get_sessionmaker(settings=settings)
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
