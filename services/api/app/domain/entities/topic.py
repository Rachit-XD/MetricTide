"""Topic entity: a canonical subject that sources can mention."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class Topic:
    """A normalized topic.

    `embedding` holds the vector representation used for clustering and
    similarity search (pgvector). It is optional until an embedding is computed.
    """

    canonical_name: str
    description: str | None = None
    embedding: list[float] | None = field(default=None, repr=False)
    # Consolidation state: merged topics are marked inactive and point at the
    # canonical topic they were merged into (audit trail).
    is_active: bool = True
    merged_into_id: UUID | None = None
    id: UUID | None = None
    created_at: datetime | None = None
