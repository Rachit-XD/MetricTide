"""SQLAlchemy implementation of :class:`TrendSnapshotRepository`."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
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
