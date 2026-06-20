"""ORM models for the DealFlow AI core schema.

Mirrors the data model in docs/architecture/v3/MASTER_BUILD_SPEC.md (§2). Tenant-
scoped tables carry ``tenant_id`` (via ``TenantMixin``) and are protected by
Row-Level Security policies defined in the Alembic migrations. Prediction and
outcome rows are treated as append-only for audit purposes.
"""

from __future__ import annotations

import datetime
import enum
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TenantMixin, TimestampMixin


# --- Enumerations -----------------------------------------------------------


class LeadTier(str, enum.Enum):
    green = "green"
    yellow = "yellow"
    red = "red"
    monitor = "monitor"


class AssignmentStatus(str, enum.Enum):
    prospect = "prospect"
    client = "client"
    past_client = "past_client"


class CallOutcome(str, enum.Enum):
    booked = "booked"
    dnc = "dnc"
    interested_future = "interested_future"
    no_contact = "no_contact"


class DealStage(str, enum.Enum):
    buyer_matching = "buyer_matching"
    loi_nda = "loi_nda"
    due_diligence = "due_diligence"
    negotiation = "negotiation"
    docs_signed = "docs_signed"
    funded = "funded"


class TaskStatus(str, enum.Enum):
    open = "open"
    done = "done"


# --- Accounts ---------------------------------------------------------------


class Tenant(TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    licensing_state: Mapped[str | None] = mapped_column(String(2))
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clerk_user_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="broker", nullable=False)
    warm_outreach_opt_in: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class BrokerParameters(TenantMixin, TimestampMixin, Base):
    """Lead-assignment gating set during onboarding (editable in Settings)."""

    __tablename__ = "broker_parameters"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    min_years_in_business: Mapped[int | None] = mapped_column(Integer)
    min_employees: Mapped[int | None] = mapped_column(Integer)
    max_employees: Mapped[int | None] = mapped_column(Integer)
    min_revenue_millions: Mapped[float | None] = mapped_column(Numeric(12, 2))
    max_revenue_millions: Mapped[float | None] = mapped_column(Numeric(12, 2))
    omitted_industries: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    omitted_locations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)


class BrokerCalendar(TenantMixin, TimestampMixin, Base):
    __tablename__ = "broker_calendars"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255))
    sync_token: Mapped[str | None] = mapped_column(Text)
    last_synced_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))


# --- Lead pool + scoring (global, not tenant-scoped) ------------------------


class RawLead(TimestampMixin, Base):
    __tablename__ = "raw_leads"

    business_name: Mapped[str] = mapped_column(String(512), nullable=False)
    dba: Mapped[str | None] = mapped_column(String(512))
    address_line1: Mapped[str | None] = mapped_column(String(512))
    city: Mapped[str | None] = mapped_column(String(255))
    state: Mapped[str | None] = mapped_column(String(2), index=True)
    postal_code: Mapped[str | None] = mapped_column(String(16))
    apn: Mapped[str | None] = mapped_column(String(64), index=True)
    naics_code: Mapped[str | None] = mapped_column(String(16))
    industry: Mapped[str | None] = mapped_column(String(255))
    employee_count: Mapped[int | None] = mapped_column(Integer)
    revenue_millions: Mapped[float | None] = mapped_column(Numeric(12, 2))
    years_in_business: Mapped[int | None] = mapped_column(Integer)
    owner_name: Mapped[str | None] = mapped_column(String(255))
    owner_email: Mapped[str | None] = mapped_column(String(320))
    owner_phone: Mapped[str | None] = mapped_column(String(64))
    owner_age: Mapped[int | None] = mapped_column(Integer)
    dedup_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    source_payloads: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class DataSourceEnrichment(TimestampMixin, Base):
    __tablename__ = "data_source_enrichment"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("raw_leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset: Mapped[str | None] = mapped_column(String(128))
    fields: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    pulled_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ModelVersion(TimestampMixin, Base):
    __tablename__ = "model_versions"

    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    artifact_uri: Mapped[str | None] = mapped_column(Text)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trained_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))


class EnsembleWeight(TimestampMixin, Base):
    __tablename__ = "ensemble_weights"

    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(6, 5), nullable=False)
    effective_from: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)


class EnsemblePrediction(TimestampMixin, Base):
    """Append-only ensemble scoring output for a lead."""

    __tablename__ = "ensemble_predictions"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("raw_leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ensemble_score: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)
    tier: Mapped[LeadTier] = mapped_column(SAEnum(LeadTier, name="lead_tier"), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    prediction_variance: Mapped[float | None] = mapped_column(Numeric(8, 5))
    model_scores: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    top_positive: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    top_negative: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    model_version_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    scored_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# --- Assignment + outreach (tenant-scoped) ----------------------------------


class LeadAssignment(TenantMixin, TimestampMixin, Base):
    """Permanent, territory-protected ownership of a lead by a broker."""

    __tablename__ = "lead_assignments"

    # One assignment per lead enforces permanent single ownership.
    lead_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("raw_leads.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tier: Mapped[LeadTier] = mapped_column(SAEnum(LeadTier, name="lead_tier"), nullable=False)
    status: Mapped[AssignmentStatus] = mapped_column(
        SAEnum(AssignmentStatus, name="assignment_status"),
        default=AssignmentStatus.prospect,
        nullable=False,
    )
    assigned_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    first_contact_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    clawed_back_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))


class LeadEmailOutreach(TenantMixin, TimestampMixin, Base):
    __tablename__ = "lead_email_outreach"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("lead_assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template: Mapped[str | None] = mapped_column(String(128))
    sent_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    opened_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    replied_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    booking_clicked_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))


class AiCallQueue(TenantMixin, TimestampMixin, Base):
    __tablename__ = "ai_call_queue"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("lead_assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    window_start: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempt_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="scheduled", nullable=False)


class AiCallOutcome(TenantMixin, TimestampMixin, Base):
    __tablename__ = "ai_call_outcomes"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("lead_assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[CallOutcome] = mapped_column(SAEnum(CallOutcome, name="call_outcome"), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    callback_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    recording_uri: Mapped[str | None] = mapped_column(Text)
    transcript_uri: Mapped[str | None] = mapped_column(Text)
    actor: Mapped[str] = mapped_column(String(32), nullable=False)
    occurred_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Appointment(TenantMixin, TimestampMixin, Base):
    __tablename__ = "appointments"

    assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("lead_assignments.id", ondelete="SET NULL"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    scheduled_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cal_event_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="booked", nullable=False)


class DealOutcome(TenantMixin, TimestampMixin, Base):
    """Closed/lost result feeding the feedback loop."""

    __tablename__ = "deal_outcomes"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("lead_assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    predicted_score: Mapped[float | None] = mapped_column(Numeric(6, 3))
    actual_outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    actual_quality_score: Mapped[float | None] = mapped_column(Numeric(6, 3))
    prediction_error: Mapped[float | None] = mapped_column(Numeric(8, 5))
    loss_reason: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# --- Deal room + pipeline (tenant-scoped) -----------------------------------


class DealRoom(TenantMixin, TimestampMixin, Base):
    __tablename__ = "deal_rooms"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("lead_assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage: Mapped[DealStage] = mapped_column(
        SAEnum(DealStage, name="deal_stage"), default=DealStage.buyer_matching, nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )


class DealRoomMessage(TenantMixin, TimestampMixin, Base):
    __tablename__ = "deal_room_messages"

    deal_room_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("deal_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender: Mapped[str] = mapped_column(String(64), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    attachment_uri: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# --- Productivity + storage (tenant-scoped) ---------------------------------


class DocumentVaultItem(TenantMixin, TimestampMixin, Base):
    __tablename__ = "document_vault"

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    doc_type: Mapped[str | None] = mapped_column(String(64))
    storage_uri: Mapped[str] = mapped_column(Text, nullable=False)
    signed_status: Mapped[str] = mapped_column(String(32), default="unsigned", nullable=False)
    linked_assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("lead_assignments.id", ondelete="SET NULL"), index=True
    )


class Task(TenantMixin, TimestampMixin, Base):
    __tablename__ = "tasks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, name="task_status"), default=TaskStatus.open, nullable=False
    )
    linked_type: Mapped[str | None] = mapped_column(String(32))
    linked_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)


class Note(TenantMixin, TimestampMixin, Base):
    __tablename__ = "notes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    body: Mapped[str | None] = mapped_column(Text)
    voice_uri: Mapped[str | None] = mapped_column(Text)
    linked_type: Mapped[str | None] = mapped_column(String(32))
    linked_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)


class WhatsappConversation(TenantMixin, TimestampMixin, Base):
    __tablename__ = "whatsapp_conversations"

    contact: Mapped[str] = mapped_column(String(64), nullable=False)
    transcript: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    last_message_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))


# --- System / admin ---------------------------------------------------------


class AdminNotification(TimestampMixin, Base):
    __tablename__ = "admin_notifications"

    level: Mapped[str] = mapped_column(String(16), default="info", nullable=False)
    source: Mapped[str | None] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class RetainedTrainingSample(TimestampMixin, Base):
    """Anonymized ML training sample retained after a tenant is purged.

    Holds only the feature vector + observed quality (no PII), so the model keeps
    learning from a departed broker's outcomes without retaining their data.
    """

    __tablename__ = "retained_training_samples"

    feature_vector: Mapped[list] = mapped_column(JSON, nullable=False)
    actual_quality_score: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)
    source_tenant_hash: Mapped[str | None] = mapped_column(String(64))


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_log"

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="SET NULL"), index=True
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(64))
    target_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
