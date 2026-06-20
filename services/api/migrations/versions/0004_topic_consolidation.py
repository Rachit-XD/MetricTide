"""topic consolidation: is_active, merged_into_id, topic_aliases

Revision ID: 0004_topic_consolidation
Revises: 0003_topic_embedding_384
Create Date: 2026-06-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_topic_consolidation"
down_revision: str | None = "0003_topic_embedding_384"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "topics",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "topics",
        sa.Column("merged_into_id", sa.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_topics_merged_into_id",
        "topics",
        "topics",
        ["merged_into_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_topics_is_active", "topics", ["is_active"])

    op.create_table(
        "topic_aliases",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("topic_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("alias", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("alias", name="uq_topic_aliases_alias"),
    )
    op.create_index("ix_topic_aliases_topic_id", "topic_aliases", ["topic_id"])


def downgrade() -> None:
    op.drop_index("ix_topic_aliases_topic_id", table_name="topic_aliases")
    op.drop_table("topic_aliases")

    op.drop_index("ix_topics_is_active", table_name="topics")
    op.drop_constraint("fk_topics_merged_into_id", "topics", type_="foreignkey")
    op.drop_column("topics", "merged_into_id")
    op.drop_column("topics", "is_active")
