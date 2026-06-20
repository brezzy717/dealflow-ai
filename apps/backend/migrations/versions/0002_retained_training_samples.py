"""Retained (anonymized) training samples for purge-on-exit.

Idempotent: the 0001 bootstrap creates tables from live ORM metadata, so on a
fresh database this table already exists by the time 0002 runs. The guards make
this migration a no-op there, while still creating the table for any database
that was stamped at 0001 before this model existed.

Revision ID: 0002_retained_training
Revises: 0001_initial
Create Date: 2026-06-20
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0002_retained_training"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "retained_training_samples"


def upgrade() -> None:
    bind = op.get_bind()
    if inspect(bind).has_table(TABLE):
        return
    op.create_table(
        TABLE,
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("feature_vector", sa.JSON(), nullable=False),
        sa.Column("actual_quality_score", sa.Numeric(6, 3), nullable=False),
        sa.Column("source_tenant_hash", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    bind = op.get_bind()
    if inspect(bind).has_table(TABLE):
        op.drop_table(TABLE)
