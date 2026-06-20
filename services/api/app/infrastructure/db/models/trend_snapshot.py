"""ORM model for the ``trend_snapshots`` table."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Double, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID  # noqa: N811  (class, not a constant)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.infrastructure.db.models.topic import TopicModel


class TrendSnapshotModel(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "trend_snapshots"
    __table_args__ = (
        UniqueConstraint("topic_id", "snapshot_date", name="uq_trend_snapshots_topic_date"),
        # "Top trends for a given day" queries.
        Index("ix_trend_snapshots_date_score", "snapshot_date", "trend_score"),
    )

    topic_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    mention_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    engagement_score: Mapped[float] = mapped_column(Double, nullable=False, default=0.0)
    growth_rate: Mapped[float] = mapped_column(Double, nullable=False, default=0.0)
    trend_score: Mapped[float] = mapped_column(Double, nullable=False, default=0.0)

    topic: Mapped[TopicModel] = relationship(back_populates="snapshots")
