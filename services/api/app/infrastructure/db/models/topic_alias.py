"""ORM model for the ``topic_aliases`` table."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID  # noqa: N811  (class, not a constant)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, TimestampMixin, UUIDMixin


class TopicAliasModel(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "topic_aliases"
    __table_args__ = (
        UniqueConstraint("alias", name="uq_topic_aliases_alias"),
        Index("ix_topic_aliases_topic_id", "topic_id"),
    )

    topic_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    alias: Mapped[str] = mapped_column(Text, nullable=False)
