"""Onboarding/settings + purge-on-exit end-to-end on Postgres (skipped locally)."""

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


def test_onboarding_settings_and_purge() -> None:
    import httpx
    from sqlalchemy import func, select

    from dealflow_backend.api.dependencies import AuthenticatedUser, get_current_user
    from dealflow_backend.core.db import get_engine, get_sessionmaker
    from dealflow_backend.db import models
    from dealflow_backend.main import app
    from dealflow_backend.services.pipeline import run_demo_pipeline

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    async def scenario() -> None:
        sm = get_sessionmaker()
        async with sm() as session:
            session.add(models.Tenant(id=tenant_id, name="Account Brokerage"))
            await session.flush()
            session.add(
                models.User(
                    id=user_id,
                    tenant_id=tenant_id,
                    clerk_user_id="clerk_account",
                    email="b@example.com",
                )
            )
            await session.commit()
            await run_demo_pipeline(
                session, tenant_id=tenant_id, user_id=user_id, lead_count=40, seed=246
            )
        # Record a graded deal outcome so there is training data to retain.
        async with sm() as session:
            assignment = (
                await session.execute(
                    select(models.LeadAssignment).where(
                        models.LeadAssignment.user_id == user_id
                    ).limit(1)
                )
            ).scalars().first()
            session.add(
                models.DealOutcome(
                    tenant_id=tenant_id,
                    assignment_id=assignment.id,
                    actual_outcome="closed",
                    actual_quality_score=88.0,
                    occurred_at=now,
                )
            )
            await session.commit()

        broker = AuthenticatedUser(user_id="clerk_account", tenant_id=str(tenant_id))
        app.dependency_overrides[get_current_user] = lambda: broker
        transport = httpx.ASGITransport(app=app)
        try:
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                # Onboarding sets parameters + opt-out.
                onboarded = await client.post(
                    "/api/onboarding",
                    json={
                        "min_years_in_business": 5,
                        "omitted_industries": ["Dry Cleaning"],
                        "warm_outreach_opt_in": False,
                    },
                )
                assert onboarded.status_code == 200
                view = (await client.get("/api/settings")).json()
                assert view["warm_outreach_opt_in"] is False
                assert view["parameters"]["min_years_in_business"] == 5

                billing = (await client.get("/api/billing/status")).json()
                assert billing["subscription_status"] == "trialing"

                # Close account -> purge.
                purge = (await client.post("/api/account/close")).json()
                assert purge["retained_samples"] >= 1
        finally:
            app.dependency_overrides.clear()

        # Tenant + its data are gone; a retained training sample remains.
        async with sm() as session:
            tenant_gone = (
                await session.execute(
                    select(func.count())
                    .select_from(models.Tenant)
                    .where(models.Tenant.id == tenant_id)
                )
            ).scalar_one()
            assert int(tenant_gone) == 0
            samples = (
                await session.execute(
                    select(func.count()).select_from(models.RetainedTrainingSample)
                )
            ).scalar_one()
            assert int(samples) >= 1

        await get_engine().dispose()

    asyncio.run(scenario())
