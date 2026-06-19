"""End-to-end slice test: ingest -> score -> assign -> Prospects API.

Requires a real Postgres (the schema + RLS). Runs in CI against the Postgres
service; skipped locally when DATABASE_URL is not Postgres. Everything runs in a
single event loop (via asyncio.run + httpx ASGITransport) so the async engine's
connections stay loop-consistent.
"""

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


def test_pipeline_end_to_end() -> None:
    import httpx

    from dealflow_backend.api.dependencies import AuthenticatedUser, get_current_user
    from dealflow_backend.core.db import get_engine, get_sessionmaker
    from dealflow_backend.db import models
    from dealflow_backend.main import app
    from dealflow_backend.services.pipeline import run_demo_pipeline

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()

    async def scenario() -> None:
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            session.add(models.Tenant(id=tenant_id, name="Test Brokerage"))
            await session.flush()
            session.add(
                models.User(
                    id=user_id,
                    tenant_id=tenant_id,
                    clerk_user_id="clerk_test_user",
                    email="broker@example.com",
                )
            )
            await session.commit()

            summary = await run_demo_pipeline(
                session,
                tenant_id=tenant_id,
                user_id=user_id,
                lead_count=40,
                seed=99,
            )

        assert summary["scored"] == 40
        assert summary["assigned"] > 0

        app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
            user_id="clerk_test_user", tenant_id=str(tenant_id)
        )
        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                response = await client.get("/api/prospects")
            assert response.status_code == 200
            prospects = response.json()["prospects"]
            assert len(prospects) == summary["assigned"]
            assert all(p["score"] is not None for p in prospects)
            assert all(
                p["tier"] in {"green", "yellow", "red", "monitor"} for p in prospects
            )
            assert any(p["explanation"] for p in prospects)
        finally:
            app.dependency_overrides.clear()
            await get_engine().dispose()

    asyncio.run(scenario())
