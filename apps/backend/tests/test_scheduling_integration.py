"""Action-gated weekly assignment, end-to-end on Postgres (skipped locally)."""

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


def test_weekly_assignment_is_action_gated() -> None:
    from sqlalchemy import select

    from dealflow_backend.core.db import get_engine, get_sessionmaker
    from dealflow_backend.db import models
    from dealflow_backend.services import scheduling

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    async def scenario() -> None:
        sm = get_sessionmaker()
        async with sm() as session:
            session.add(models.Tenant(id=tenant_id, name="Sched Brokerage"))
            await session.flush()
            session.add(
                models.User(
                    id=user_id,
                    tenant_id=tenant_id,
                    clerk_user_id="clerk_sched",
                    email="b@example.com",
                )
            )
            await session.commit()

        # refresh -> pool of scored leads.
        async with sm() as session:
            refresh = await scheduling.run_job("refresh", session)
            assert refresh["scored"] == 40

        # First weekly drop: broker is eligible (no outstanding) -> gets leads.
        async with sm() as session:
            first = await scheduling.assign_weekly(session, now=now)
            assert first[str(user_id)]["assigned"] > 0

        # Backdate one prospect past the grace window with no outcome.
        async with sm() as session:
            assignment = (
                await session.execute(select(models.LeadAssignment).limit(1))
            ).scalar_one()
            assignment.assigned_at = now - datetime.timedelta(days=10)
            await session.commit()
            outstanding = await scheduling.count_outstanding_prospects(
                session, user_id=user_id, now=now
            )
            assert outstanding >= 1

        # Second drop: broker now ineligible -> skipped.
        async with sm() as session:
            second = await scheduling.assign_weekly(session, now=now)
            assert second[str(user_id)]["assigned"] == 0
            assert second[str(user_id)]["skipped_outstanding"] >= 1

        await get_engine().dispose()

    asyncio.run(scenario())
