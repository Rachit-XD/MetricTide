"""ORM model for the ``sources`` table."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.platform import Platform
from app.infrastructure.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.infrastructure.db.models.topic_mention import TopicMentionModel


class SourceModel(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("platform", "external_id", name="uq_sources_platform_external_id"),
        Index("ix_sources_created_at", "created_at"),
    )

    platform: Mapped[Platform] = mapped_column(
        SAEnum(
            Platform,
            name="platform_enum",
            native_enum=True,
            validate_strings=True,
            # Store the enum *value* ("reddit"), not its name ("REDDIT"), to
            # match the DB enum type created by the migration.
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    mentions: Mapped[list["TopicMentionModel"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
