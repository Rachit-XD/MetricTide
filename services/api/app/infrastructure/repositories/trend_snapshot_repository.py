"""SQLAlchemy implementation of :class:`TrendSnapshotRepository`."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.trend_snapshot import TrendSnapshot
from app.domain.repositories.trend_snapshot_repository import TrendSnapshotRepository
from app.infrastructure.db.models.trend_snapshot import TrendSnapshotModel
from app.infrastructure.repositories.mappers import (
    trend_snapshot_to_entity,
    trend_snapshot_to_model,
)


class SqlAlchemyTrendSnapshotRepository(TrendSnapshotRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, snapshot: TrendSnapshot) -> TrendSnapshot:
        model = trend_snapshot_to_model(snapshot)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return trend_snapshot_to_entity(model)

    async def get_for_topic_on_date(
        self, topic_id: UUID, snapshot_date: date
    ) -> TrendSnapshot | None:
        stmt = select(TrendSnapshotModel).where(
            TrendSnapshotModel.topic_id == topic_id,
            TrendSnapshotModel.snapshot_date == snapshot_date,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return trend_snapshot_to_entity(model) if model is not None else None

    async def list_top_for_date(
        self, snapshot_date: date, limit: int = 20
    ) -> list[TrendSnapshot]:
        stmt = (
            select(TrendSnapshotModel)
            .where(TrendSnapshotModel.snapshot_date == snapshot_date)
            .order_by(TrendSnapshotModel.trend_score.desc())
            .limit(limit)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [trend_snapshot_to_entity(m) for m in models]

    async def upsert(self, snapshot: TrendSnapshot) -> None:
        # One snapshot per (topic, date): re-running the same day updates in place.
        values = {
            "topic_id": snapshot.topic_id,
            "snapshot_date": snapshot.snapshot_date,
            "mention_count": snapshot.mention_count,
            "engagement_score": snapshot.engagement_score,
            "growth_rate": snapshot.growth_rate,
            "trend_score": snapshot.trend_score,
        }
        stmt = pg_insert(TrendSnapshotModel).values(**values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_trend_snapshots_topic_date",
            set_={
                "mention_count": stmt.excluded.mention_count,
                "engagement_score": stmt.excluded.engagement_score,
                "growth_rate": stmt.excluded.growth_rate,
                "trend_score": stmt.excluded.trend_score,
            },
        )
        await self._session.execute(stmt)

    async def get_latest_before(
        self, topic_id: UUID, before_date: date
    ) -> TrendSnapshot | None:
        stmt = (
            select(TrendSnapshotModel)
            .where(
                TrendSnapshotModel.topic_id == topic_id,
                TrendSnapshotModel.snapshot_date < before_date,
            )
            .order_by(TrendSnapshotModel.snapshot_date.desc())
            .limit(1)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return trend_snapshot_to_entity(model) if model is not None else None
