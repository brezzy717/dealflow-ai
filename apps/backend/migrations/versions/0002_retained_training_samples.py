"""Retained (anonymized) training samples for purge-on-exit.

Revision ID: 0002_retained_training
Revises: 0001_initial
Create Date: 2026-06-20
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_retained_training"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "retained_training_samples",
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
    op.drop_table("retained_training_samples")
