"""Deal Room + pipeline end-to-end on Postgres (skipped locally)."""

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


def test_deal_room_lifecycle() -> None:
    import httpx
    from sqlalchemy import select

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
            session.add(models.Tenant(id=tenant_id, name="DealRoom Brokerage"))
            await session.flush()
            session.add(
                models.User(
                    id=user_id,
                    tenant_id=tenant_id,
                    clerk_user_id="clerk_room",
                    email="b@example.com",
                )
            )
            await session.commit()
            await run_demo_pipeline(
                session, tenant_id=tenant_id, user_id=user_id, lead_count=40, seed=555
            )
        # Promote one assignment to client so it can enter the pipeline.
        async with sm() as session:
            assignment = (
                await session.execute(
                    select(models.LeadAssignment).where(
                        models.LeadAssignment.user_id == user_id
                    ).limit(1)
                )
            ).scalars().first()
            assignment.status = models.AssignmentStatus.client
            assignment_id = assignment.id
            await session.commit()

        broker = AuthenticatedUser(user_id="clerk_room", tenant_id=str(tenant_id))
        app.dependency_overrides[get_current_user] = lambda: broker
        transport = httpx.ASGITransport(app=app)
        try:
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                opened = (await client.post(f"/api/pipeline/{assignment_id}/open")).json()
                assert opened["created"] is True
                room_id = opened["id"]

                # Advance stage.
                staged = await client.post(
                    f"/api/deal-rooms/{room_id}/stage", json={"stage": "due_diligence"}
                )
                assert staged.json()["stage"] == "due_diligence"

                # Post a message + attach a document.
                msg = await client.post(
                    f"/api/deal-rooms/{room_id}/messages",
                    json={"sender": "broker", "body": "Welcome to the deal room"},
                )
                assert msg.status_code == 200
                doc = await client.post(
                    f"/api/deal-rooms/{room_id}/documents",
                    json={"name": "NDA.pdf", "storage_uri": "s3://x/nda.pdf"},
                )
                assert doc.status_code == 200

                room = (await client.get(f"/api/deal-rooms/{room_id}")).json()
                assert len(room["messages"]) == 1

                pipeline = (await client.get("/api/pipeline")).json()["deals"]
                assert any(d["id"] == room_id for d in pipeline)

                # Close -> archive to past-client.
                closed = (await client.post(f"/api/deal-rooms/{room_id}/close")).json()
                assert closed["archived"] is True

            async with sm() as session:
                assignment = (
                    await session.execute(
                        select(models.LeadAssignment).where(
                            models.LeadAssignment.id == assignment_id
                        )
                    )
                ).scalar_one()
                assert assignment.status == models.AssignmentStatus.past_client
        finally:
            app.dependency_overrides.clear()
            await get_engine().dispose()

    asyncio.run(scenario())
