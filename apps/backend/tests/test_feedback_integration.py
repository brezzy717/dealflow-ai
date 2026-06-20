"""End-to-end feedback loop test: outcomes -> retrain -> new model version.

Requires Postgres (RLS + schema); skipped locally. Runs the pipeline, records
deal outcomes through the API, triggers an admin retrain, and asserts a new
active model version and adaptive weights were persisted.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import uuid

import pytest

DATABASE_URL = os.getenv("DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL.startswith("postgresql"),
    reason="integration test requires a Postgres DATABASE_URL",
)


def test_feedback_loop_end_to_end() -> None:
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
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            session.add(models.Tenant(id=tenant_id, name="Feedback Brokerage"))
            await session.flush()
            session.add(
                models.User(
                    id=user_id,
                    tenant_id=tenant_id,
                    clerk_user_id="clerk_feedback_user",
                    email="broker@example.com",
                )
            )
            await session.commit()
            await run_demo_pipeline(
                session, tenant_id=tenant_id, user_id=user_id, lead_count=40, seed=123
            )

        broker = AuthenticatedUser(user_id="clerk_feedback_user", tenant_id=str(tenant_id))
        app.dependency_overrides[get_current_user] = lambda: broker
        transport = httpx.ASGITransport(app=app)
        try:
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                prospects = (await client.get("/api/prospects")).json()["prospects"]
                assert len(prospects) >= 12
                ids = [p["assignment_id"] for p in prospects]

                # First contact on one prospect.
                call = await client.post(
                    f"/api/prospects/{ids[0]}/call-outcome", json={"outcome": "booked"}
                )
                assert call.status_code == 200

                # Record 12 graded deal outcomes to feed the retrainer.
                for i, assignment_id in enumerate(ids[:12]):
                    quality = 90.0 if i % 2 == 0 else 15.0
                    deal = await client.post(
                        f"/api/prospects/{assignment_id}/deal-outcome",
                        json={
                            "outcome": "closed" if quality > 50 else "lost",
                            "quality_score": quality,
                        },
                    )
                    assert deal.status_code == 200

            # Admin retrain.
            with tempfile.TemporaryDirectory() as artifacts:
                os.environ["MODEL_ARTIFACTS_DIR"] = artifacts
                from dealflow_backend.services.retraining import retrain_from_feedback

                async with get_sessionmaker()() as session:
                    result = await retrain_from_feedback(
                        session, artifacts_dir=artifacts, min_samples=10
                    )
                assert result["status"] == "retrained"
                assert result["samples"] >= 12
                assert abs(sum(result["weights"].values()) - 1.0) < 1e-6

                async with get_sessionmaker()() as session:
                    active = (
                        await session.execute(
                            select(func.count())
                            .select_from(models.ModelVersion)
                            .where(models.ModelVersion.is_active.is_(True))
                        )
                    ).scalar_one()
                    weights = (
                        await session.execute(
                            select(func.count()).select_from(models.EnsembleWeight)
                        )
                    ).scalar_one()
                assert active == 3
                assert weights == 3
        finally:
            app.dependency_overrides.clear()
            await get_engine().dispose()

    asyncio.run(scenario())
