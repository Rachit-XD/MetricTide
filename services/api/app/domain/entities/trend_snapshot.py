"""TrendSnapshot entity: per-topic trend metrics captured for a given date."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(slots=True)
class TrendSnapshot:
    """A point-in-time measurement of a topic's momentum.

    One snapshot is expected per topic per `snapshot_date`. `created_at` records
    when the snapshot row was written (audit), distinct from the logical
    `snapshot_date` it describes.
    """

    topic_id: UUID
    snapshot_date: date
    mention_count: int
    engagement_score: float
    growth_rate: float
    trend_score: float
    id: UUID | None = None
    created_at: datetime | None = None
