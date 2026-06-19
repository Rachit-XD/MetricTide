"""initial schema: sources, topics, topic_mentions, trend_snapshots

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIM = 1536


def upgrade() -> None:
    # Required extensions (idempotent; also enabled by the Docker init script).
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # `create_type=False` keeps create_table from re-emitting CREATE TYPE; we
    # create the enum explicitly (idempotently) here instead.
    platform_enum = postgresql.ENUM(
        "reddit", "hackernews", name="platform_enum", create_type=False
    )
    platform_enum.create(op.get_bind(), checkfirst=True)

    # ---- sources ----
    op.create_table(
        "sources",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "platform", "external_id", name="uq_sources_platform_external_id"
        ),
    )
    op.create_index("ix_sources_created_at", "sources", ["created_at"])

    # ---- topics ----
    op.create_table(
        "topics",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("canonical_name", name="uq_topics_canonical_name"),
    )
    op.create_index(
        "ix_topics_embedding_hnsw",
        "topics",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    # ---- topic_mentions ----
    op.create_table(
        "topic_mentions",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("source_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("confidence_score", sa.Double(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["sources.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"], ["topics.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "source_id", "topic_id", name="uq_topic_mentions_source_topic"
        ),
    )
    op.create_index("ix_topic_mentions_topic_id", "topic_mentions", ["topic_id"])
    op.create_index("ix_topic_mentions_source_id", "topic_mentions", ["source_id"])

    # ---- trend_snapshots ----
    op.create_table(
        "trend_snapshots",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("topic_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("mention_count", sa.Integer(), nullable=False),
        sa.Column("engagement_score", sa.Double(), nullable=False),
        sa.Column("growth_rate", sa.Double(), nullable=False),
        sa.Column("trend_score", sa.Double(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"], ["topics.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "topic_id", "snapshot_date", name="uq_trend_snapshots_topic_date"
        ),
    )
    op.create_index(
        "ix_trend_snapshots_date_score",
        "trend_snapshots",
        ["snapshot_date", "trend_score"],
    )


def downgrade() -> None:
    op.drop_index("ix_trend_snapshots_date_score", table_name="trend_snapshots")
    op.drop_table("trend_snapshots")

    op.drop_index("ix_topic_mentions_source_id", table_name="topic_mentions")
    op.drop_index("ix_topic_mentions_topic_id", table_name="topic_mentions")
    op.drop_table("topic_mentions")

    op.drop_index("ix_topics_embedding_hnsw", table_name="topics")
    op.drop_table("topics")

    op.drop_index("ix_sources_created_at", table_name="sources")
    op.drop_table("sources")

    postgresql.ENUM(name="platform_enum", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
