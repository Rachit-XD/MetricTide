"""ORM model for the ``topics`` table."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.infrastructure.db.models.topic_mention import TopicMentionModel
    from app.infrastructure.db.models.trend_snapshot import TrendSnapshotModel

# Dimensionality of topic embeddings (sentence-transformers all-MiniLM-L6-v2).
EMBEDDING_DIM = 384


class TopicModel(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "topics"
    __table_args__ = (
        # Approximate nearest-neighbour index for cosine similarity search.
        Index(
            "ix_topics_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    mentions: Mapped[list[TopicMentionModel]] = relationship(
        back_populates="topic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    snapshots: Mapped[list[TrendSnapshotModel]] = relationship(
        back_populates="topic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
