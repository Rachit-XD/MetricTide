"""Declarative base and shared column mixins for SQLAlchemy ORM models.

ORM models subclass ``Base`` and reuse ``UUIDMixin`` / ``TimestampMixin`` for
the conventions applied across every table:

* UUID primary keys generated server-side via ``gen_random_uuid()`` (pgcrypto).
* Timezone-aware ``created_at`` defaulted to ``now()`` by the database.

Alembic imports the models package so ``Base.metadata`` is fully populated for
autogeneration.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Common declarative base for all ORM models."""


class UUIDMixin:
    """Adds a server-generated UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )


class TimestampMixin:
    """Adds a timezone-aware ``created_at`` timestamp."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
