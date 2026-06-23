"""Initial schema + Row-Level Security.

Bootstraps every core table from the ORM metadata, then enables and FORCEs
Row-Level Security on tenant-scoped tables. Policies match rows against the
``app.current_tenant`` session variable set by
``dealflow_backend.core.db.set_current_tenant``. With ``missing_ok => true``,
an unset variable yields NULL and the policy denies by default. Cross-tenant
system jobs (e.g. the assignment engine) connect with a role that has
BYPASSRLS or set the tenant per write.

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-19
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from dealflow_backend.db import Base
from dealflow_backend.db import models  # noqa: F401  (populate Base.metadata)

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Tenant-scoped tables carrying a tenant_id column protected by RLS.
TENANT_SCOPED_TABLES: tuple[str, ...] = (
    "users",
    "broker_parameters",
    "broker_calendars",
    "lead_assignments",
    "lead_email_outreach",
    "ai_call_queue",
    "ai_call_outcomes",
    "appointments",
    "deal_outcomes",
    "deal_rooms",
    "deal_room_messages",
    "document_vault",
    "tasks",
    "notes",
    "whatsapp_conversations",
)


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

    for table in TENANT_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
            USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid)
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    for table in TENANT_SCOPED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    Base.metadata.drop_all(bind=bind)
