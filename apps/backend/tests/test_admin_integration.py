"""Admin APIs end-to-end on Postgres (skipped locally)."""

from __future__ import annotations

import asyncio
import os
import uuid

import pytest

DATABASE_URL = os.getenv("DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL.startswith("postgresql"),
    reason="integration test requires a Postgres DATABASE_URL",
)


def test_admin_health_and_clawback() -> None:
    import httpx
    from sqlalchemy import func, select

    from dealflow_backend.api.dependencies import AuthenticatedUser, get_current_user
    from dealflow_backend.core.db import get_engine, get_sessionmaker
    from dealflow_backend.db import models
    from dealflow_backend.main import app
    from dealflow_backend.services.pipeline import run_demo_pipeline

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()

    async def scenario() -> None:
        sm = get_sessionmaker()
        async with sm() as session:
            session.add(models.Tenant(id=tenant_id, name="Admin Brokerage"))
            await session.flush()
            session.add(
                models.User(
                    id=user_id,
                    tenant_id=tenant_id,
                    clerk_user_id="clerk_admin_target",
                    email="b@example.com",
                )
            )
            await session.commit()
            await run_demo_pipeline(
                session, tenant_id=tenant_id, user_id=user_id, lead_count=40, seed=909
            )

        async with sm() as session:
            assignment_id = (
                await session.execute(
                    select(models.LeadAssignment.id).where(
                        models.LeadAssignment.user_id == user_id
                    ).limit(1)
                )
            ).scalar_one()

        admin = AuthenticatedUser(
            user_id="admin_user", tenant_id=str(tenant_id), claims={"role": "admin"}
        )
        app.dependency_overrides[get_current_user] = lambda: admin
        transport = httpx.ASGITransport(app=app)
        try:
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                health = (await client.get("/api/admin/health")).json()
                assert health["assignments"] >= 1
                assert "unacknowledged_alerts" in health

                users = (await client.get("/api/admin/users")).json()["users"]
                assert any(u["id"] == str(user_id) for u in users)

                # Clawback re-pools the lead and writes an audit entry.
                clawed = (
                    await client.post(f"/api/admin/clawback/{assignment_id}")
                ).json()
                assert clawed["clawed_back"] is True

                audit = (await client.get("/api/admin/audit")).json()["audit"]
                assert any(
                    a["action"] == "lead_clawback"
                    and a["target_id"] == str(assignment_id)
                    for a in audit
                )

            async with sm() as session:
                gone = (
                    await session.execute(
                        select(func.count())
                        .select_from(models.LeadAssignment)
                        .where(models.LeadAssignment.id == assignment_id)
                    )
                ).scalar_one()
                assert int(gone) == 0
        finally:
            app.dependency_overrides.clear()
            await get_engine().dispose()

    asyncio.run(scenario())
