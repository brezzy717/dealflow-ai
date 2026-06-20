"""Deal Room + PipeDeal APIs (spec §7).

A Deal Room spins up when a client enters the pipeline. It carries the Kanban
stage, a multi-party message thread, and attached documents. Reaching the final
stage and closing archives the client to past-client. Realtime delivery
(Supabase Realtime) + e-signature + push are tracked gaps; messages are durable
and polled today.
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from ..db import models
from .context import BrokerContext, get_broker_context

router = APIRouter(prefix="/api", tags=["dealroom"])

STAGE_ORDER: tuple[models.DealStage, ...] = (
    models.DealStage.buyer_matching,
    models.DealStage.loi_nda,
    models.DealStage.due_diligence,
    models.DealStage.negotiation,
    models.DealStage.docs_signed,
    models.DealStage.funded,
)


async def _owned_room(ctx: BrokerContext, room_id: uuid.UUID) -> models.DealRoom:
    """Load a deal room and verify it belongs to the broker's assignments."""
    assert ctx.user is not None
    room = (
        await ctx.session.execute(
            select(models.DealRoom)
            .join(
                models.LeadAssignment,
                models.LeadAssignment.id == models.DealRoom.assignment_id,
            )
            .where(
                models.DealRoom.id == room_id,
                models.LeadAssignment.user_id == ctx.user.id,
            )
        )
    ).scalar_one_or_none()
    if room is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deal room not found.")
    return room


@router.post("/pipeline/{assignment_id}/open")
async def open_deal_room(
    assignment_id: uuid.UUID, ctx: BrokerContext = Depends(get_broker_context)
) -> dict:
    """Spin up a Deal Room for one of the broker's client assignments."""
    if ctx.user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker.")
    assignment = (
        await ctx.session.execute(
            select(models.LeadAssignment).where(
                models.LeadAssignment.id == assignment_id,
                models.LeadAssignment.user_id == ctx.user.id,
            )
        )
    ).scalar_one_or_none()
    if assignment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found.")

    existing = (
        await ctx.session.execute(
            select(models.DealRoom).where(
                models.DealRoom.assignment_id == assignment_id
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return {"id": str(existing.id), "stage": existing.stage.value, "created": False}

    room = models.DealRoom(
        tenant_id=assignment.tenant_id,
        assignment_id=assignment_id,
        created_by_user_id=ctx.user.id,
    )
    ctx.session.add(room)
    await ctx.session.commit()
    return {"id": str(room.id), "stage": room.stage.value, "created": True}


@router.get("/pipeline")
async def list_pipeline(ctx: BrokerContext = Depends(get_broker_context)) -> dict:
    """Kanban data: the broker's deal rooms grouped by stage."""
    if ctx.user is None:
        return {"deals": []}
    rows = (
        await ctx.session.execute(
            select(models.DealRoom, models.RawLead)
            .join(
                models.LeadAssignment,
                models.LeadAssignment.id == models.DealRoom.assignment_id,
            )
            .join(models.RawLead, models.RawLead.id == models.LeadAssignment.lead_id)
            .where(models.LeadAssignment.user_id == ctx.user.id)
        )
    ).all()
    return {
        "deals": [
            {
                "id": str(room.id),
                "stage": room.stage.value,
                "status": room.status,
                "business_name": lead.business_name,
            }
            for room, lead in rows
        ]
    }


class StageIn(BaseModel):
    stage: str


@router.post("/deal-rooms/{room_id}/stage")
async def set_stage(
    room_id: uuid.UUID, body: StageIn, ctx: BrokerContext = Depends(get_broker_context)
) -> dict:
    if ctx.user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker.")
    try:
        target = models.DealStage(body.stage)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid stage.") from exc
    room = await _owned_room(ctx, room_id)
    room.stage = target
    await ctx.session.commit()
    return {"id": str(room.id), "stage": room.stage.value}


@router.get("/deal-rooms/{room_id}")
async def get_deal_room(
    room_id: uuid.UUID, ctx: BrokerContext = Depends(get_broker_context)
) -> dict:
    if ctx.user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker.")
    room = await _owned_room(ctx, room_id)
    messages = (
        await ctx.session.execute(
            select(models.DealRoomMessage)
            .where(models.DealRoomMessage.deal_room_id == room_id)
            .order_by(models.DealRoomMessage.sent_at.asc())
        )
    ).scalars().all()
    return {
        "id": str(room.id),
        "stage": room.stage.value,
        "status": room.status,
        "messages": [
            {
                "id": str(m.id),
                "sender": m.sender,
                "body": m.body,
                "attachment_uri": m.attachment_uri,
                "sent_at": m.sent_at.isoformat(),
            }
            for m in messages
        ],
    }


class MessageIn(BaseModel):
    sender: str
    body: str | None = None
    attachment_uri: str | None = None


@router.post("/deal-rooms/{room_id}/messages")
async def post_message(
    room_id: uuid.UUID, body: MessageIn, ctx: BrokerContext = Depends(get_broker_context)
) -> dict:
    if ctx.user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker.")
    room = await _owned_room(ctx, room_id)
    message = models.DealRoomMessage(
        tenant_id=room.tenant_id,
        deal_room_id=room.id,
        sender=body.sender,
        body=body.body,
        attachment_uri=body.attachment_uri,
        sent_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    ctx.session.add(message)
    await ctx.session.commit()
    return {"id": str(message.id), "created": True}


class DocumentIn(BaseModel):
    name: str
    storage_uri: str
    doc_type: str | None = None


@router.post("/deal-rooms/{room_id}/documents")
async def attach_document(
    room_id: uuid.UUID, body: DocumentIn, ctx: BrokerContext = Depends(get_broker_context)
) -> dict:
    """One-click attach a document to the room's client."""
    if ctx.user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker.")
    room = await _owned_room(ctx, room_id)
    doc = models.DocumentVaultItem(
        tenant_id=room.tenant_id,
        owner_user_id=ctx.user.id,
        name=body.name,
        doc_type=body.doc_type,
        storage_uri=body.storage_uri,
        linked_assignment_id=room.assignment_id,
    )
    ctx.session.add(doc)
    await ctx.session.commit()
    return {"id": str(doc.id), "created": True}


@router.post("/deal-rooms/{room_id}/close")
async def close_deal(
    room_id: uuid.UUID, ctx: BrokerContext = Depends(get_broker_context)
) -> dict:
    """Funded/complete: close the room and archive the client to past-client."""
    if ctx.user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker.")
    room = await _owned_room(ctx, room_id)
    room.status = "closed"
    room.stage = models.DealStage.funded
    assignment = (
        await ctx.session.execute(
            select(models.LeadAssignment).where(
                models.LeadAssignment.id == room.assignment_id
            )
        )
    ).scalar_one()
    assignment.status = models.AssignmentStatus.past_client
    await ctx.session.commit()
    return {"id": str(room.id), "status": room.status, "archived": True}
