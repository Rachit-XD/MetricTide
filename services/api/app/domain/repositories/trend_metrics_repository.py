"""Trend metrics read-model port.

Read-only aggregations that span Source + TopicMention + Topic, used by trend
scoring. Kept separate from the write repositories because it is a query/read
model, not an aggregate persistence contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TopicMetrics:
    """Aggregated signal for one topic, used as scoring input."""

    topic_id: UUID
    canonical_name: str
    mention_count: int
    engagement_score: float  # sum of source scores
    platform_count: int  # distinct platforms mentioning the topic
    latest_source_at: datetime | None  # most recent effective source timestamp


@dataclass(frozen=True, slots=True)
class TrendRanking:
    """One row of the trend ranking (read from stored snapshots)."""

    canonical_name: str
    mention_count: int
    engagement_score: float
    trend_score: float
    snapshot_date: date


class TrendMetricsRepository(ABC):
    @abstractmethod
    async def topic_metrics(self) -> list[TopicMetrics]:
        """Aggregate scoring metrics for every topic that has mentions."""

    @abstractmethod
    async def top_trends(self, limit: int = 20) -> list[TrendRanking]:
        """Return the top-ranked topics from the most recent snapshot date."""
