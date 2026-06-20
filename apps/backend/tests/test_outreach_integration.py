"""Outreach flow end-to-end on Postgres (skipped locally).

Pipeline -> Day-0 emails + queued calls -> AI concierge works the due queue,
records no-contact outcomes, and reschedules the second call. Scoped to its own
tenant for determinism in the shared CI database.
"""

from __future__ import annotations

import asyncio
import datetime
import os
import uuid

import pytest

DATABASE_URL = os.getenv("DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL.startswith("postgresql"),
    reason="integration test requires a Postgres DATABASE_URL",
)


def test_outreach_email_and_concierge() -> None:
    from sqlalchemy import func, select, update

    from dealflow_backend.core.db import get_engine, get_sessionmaker
    from dealflow_backend.db import models
    from dealflow_backend.services.outreach.service import (
        run_concierge,
        start_outreach_for_new_assignments,
    )
    from dealflow_backend.services.pipeline import run_demo_pipeline

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    async def count(session, model) -> int:
        return int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(model)
                    .where(model.tenant_id == tenant_id)
                )
            ).scalar_one()
        )

    async def scenario() -> None:
        sm = get_sessionmaker()
        async with sm() as session:
            session.add(models.Tenant(id=tenant_id, name="Outreach Brokerage"))
            await session.flush()
            session.add(
                models.User(
                    id=user_id,
                    tenant_id=tenant_id,
                    clerk_user_id="clerk_outreach",
                    email="b@example.com",
                    warm_outreach_opt_in=True,
                )
            )
            await session.commit()
            summary = await run_demo_pipeline(
                session, tenant_id=tenant_id, user_id=user_id, lead_count=40, seed=321
            )
        assigned = summary["assigned"]

        # Day-0 emails + queued Day-7 calls.
        async with sm() as session:
            out = await start_outreach_for_new_assignments(session, tenant_id=tenant_id)
            assert out["emails_sent"] == assigned
            assert out["calls_queued"] == assigned
            assert await count(session, models.LeadEmailOutreach) == assigned
            assert await count(session, models.AiCallQueue) == assigned

        # Make the queued calls due, then run the concierge.
        async with sm() as session:
            await session.execute(
                update(models.AiCallQueue)
                .where(models.AiCallQueue.tenant_id == tenant_id)
                .values(window_start=now - datetime.timedelta(hours=1))
            )
            await session.commit()
            result = await run_concierge(session, now=now, tenant_id=tenant_id)
            assert result["calls_placed"] == assigned

        async with sm() as session:
            outcomes = await count(session, models.AiCallOutcome)
            assert outcomes == assigned
            # No-contact reschedules a second attempt, so a new scheduled call exists.
            second = (
                await session.execute(
                    select(func.count())
                    .select_from(models.AiCallQueue)
                    .where(
                        models.AiCallQueue.tenant_id == tenant_id,
                        models.AiCallQueue.attempt_no == 2,
                        models.AiCallQueue.status == "scheduled",
                    )
                )
            ).scalar_one()
            assert int(second) == assigned

        await get_engine().dispose()

    asyncio.run(scenario())
