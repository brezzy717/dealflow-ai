"""Dashboard APIs end-to-end on Postgres (skipped locally)."""

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


def test_dashboard_flow() -> None:
    import httpx
    from sqlalchemy import select

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
            session.add(models.Tenant(id=tenant_id, name="Dash Brokerage"))
            await session.flush()
            session.add(
                models.User(
                    id=user_id,
                    tenant_id=tenant_id,
                    clerk_user_id="clerk_dash",
                    email="b@example.com",
                )
            )
            await session.commit()
            summary = await run_demo_pipeline(
                session, tenant_id=tenant_id, user_id=user_id, lead_count=40, seed=777
            )
        total = summary["assigned"]

        # Convert one prospect into a closed client + book an appointment.
        async with sm() as session:
            assignment = (
                await session.execute(
                    select(models.LeadAssignment).where(
                        models.LeadAssignment.user_id == user_id
                    ).limit(1)
                )
            ).scalars().first()
            assignment.status = models.AssignmentStatus.client
            session.add(
                models.DealOutcome(
                    tenant_id=tenant_id,
                    assignment_id=assignment.id,
                    actual_outcome="closed",
                    actual_quality_score=90.0,
                    occurred_at=now,
                )
            )
            session.add(
                models.Appointment(
                    tenant_id=tenant_id,
                    assignment_id=assignment.id,
                    user_id=user_id,
                    source="manual",
                    scheduled_at=now,
                    status="booked",
                )
            )
            await session.commit()

        broker = AuthenticatedUser(user_id="clerk_dash", tenant_id=str(tenant_id))
        app.dependency_overrides[get_current_user] = lambda: broker
        transport = httpx.ASGITransport(app=app)
        try:
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                metrics = (await client.get("/api/metrics")).json()
                assert metrics["clients"] == 1
                assert metrics["closed_deals"] == 1
                assert metrics["appointments"] == 1
                assert metrics["prospects"] == total - 1

                clients = (await client.get("/api/clients")).json()["clients"]
                assert len(clients) == 1

                created = await client.post(
                    "/api/tasks", json={"title": "Call back owner"}
                )
                assert created.status_code == 200
                tasks = (await client.get("/api/tasks")).json()["tasks"]
                assert len(tasks) == 1

                summary_rep = (await client.get("/api/reports/summary")).json()
                assert sum(summary_rep["by_tier"].values()) == total

                as_json = (await client.get("/api/export/prospects?format=json")).json()
                assert len(as_json["prospects"]) == total
                csv_resp = await client.get("/api/export/prospects?format=csv")
                assert csv_resp.status_code == 200
                assert "text/csv" in csv_resp.headers["content-type"]
        finally:
            app.dependency_overrides.clear()
            await get_engine().dispose()

    asyncio.run(scenario())
