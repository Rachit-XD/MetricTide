"""Source entity: a single raw item ingested from an external platform."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.entities.platform import Platform


@dataclass(slots=True)
class Source:
    """A raw signal (e.g. a Reddit post) pulled from a platform.

    `id` and `created_at` are assigned by the persistence layer, so they are
    optional until the entity has been stored.
    """

    platform: Platform
    external_id: str
    title: str
    content: str | None = None
    author: str | None = None
    score: int | None = None
    url: str | None = None
    # Original publication time at the source (distinct from `created_at`, which
    # is when we ingested the row). Optional: not every source exposes it.
    source_created_at: datetime | None = None
    id: UUID | None = None
    created_at: datetime | None = None
