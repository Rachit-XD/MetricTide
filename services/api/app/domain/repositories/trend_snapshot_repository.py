"""TrendSnapshot repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.domain.entities.trend_snapshot import TrendSnapshot


class TrendSnapshotRepository(ABC):
    """Persistence contract for :class:`TrendSnapshot` aggregates."""

    @abstractmethod
    async def add(self, snapshot: TrendSnapshot) -> TrendSnapshot:
        """Persist a new snapshot and return it with its assigned id."""

    @abstractmethod
    async def get_for_topic_on_date(
        self, topic_id: UUID, snapshot_date: date
    ) -> TrendSnapshot | None:
        """Return the snapshot for a topic on a given date, or ``None``."""

    @abstractmethod
    async def list_top_for_date(
        self, snapshot_date: date, limit: int = 20
    ) -> list[TrendSnapshot]:
        """Return the highest-scoring snapshots for a given date."""
