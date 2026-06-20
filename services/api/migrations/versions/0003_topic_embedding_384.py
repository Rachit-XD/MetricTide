"""change topics.embedding dimension from 1536 to 384

Revision ID: 0003_topic_embedding_384
Revises: 0002_add_source_created_at
Create Date: 2026-06-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "0003_topic_embedding_384"
down_revision: str | None = "0002_add_source_created_at"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_HNSW_KW = {
    "postgresql_using": "hnsw",
    "postgresql_with": {"m": 16, "ef_construction": 64},
    "postgresql_ops": {"embedding": "vector_cosine_ops"},
}


def _swap_embedding(dim: int) -> None:
    # Existing embeddings are all NULL, so dropping and re-adding the column is
    # the cleanest way to change the vector dimension (no cast needed).
    op.drop_index("ix_topics_embedding_hnsw", table_name="topics")
    op.drop_column("topics", "embedding")
    op.add_column("topics", sa.Column("embedding", Vector(dim), nullable=True))
    op.create_index("ix_topics_embedding_hnsw", "topics", ["embedding"], **_HNSW_KW)


def upgrade() -> None:
    _swap_embedding(384)


def downgrade() -> None:
    _swap_embedding(1536)
