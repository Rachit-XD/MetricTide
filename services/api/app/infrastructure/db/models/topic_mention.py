"""ORM model for the ``topic_mentions`` table."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Double, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.infrastructure.db.models.source import SourceModel
    from app.infrastructure.db.models.topic import TopicModel


class TopicMentionModel(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "topic_mentions"
    __table_args__ = (
        UniqueConstraint("source_id", "topic_id", name="uq_topic_mentions_source_topic"),
        Index("ix_topic_mentions_topic_id", "topic_id"),
        Index("ix_topic_mentions_source_id", "source_id"),
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    confidence_score: Mapped[float] = mapped_column(Double, nullable=False)

    source: Mapped["SourceModel"] = relationship(back_populates="mentions")
    topic: Mapped["TopicModel"] = relationship(back_populates="mentions")
