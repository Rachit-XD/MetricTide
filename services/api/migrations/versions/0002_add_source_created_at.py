"""add sources.source_created_at

Revision ID: 0002_add_source_created_at
Revises: 0001_initial_schema
Create Date: 2026-06-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_add_source_created_at"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nullable: existing rows keep NULL (original publication time unknown).
    op.add_column(
        "sources",
        sa.Column("source_created_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Supports time-window queries (e.g. trend detection) over publication time.
    op.create_index(
        "ix_sources_source_created_at", "sources", ["source_created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_sources_source_created_at", table_name="sources")
    op.drop_column("sources", "source_created_at")
