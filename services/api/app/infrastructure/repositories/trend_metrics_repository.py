"""SQLAlchemy implementation of the trend metrics read model."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.trend_metrics_repository import (
    TopicMetrics,
    TrendMetricsRepository,
    TrendRanking,
)
from app.infrastructure.db.models.source import SourceModel
from app.infrastructure.db.models.topic import TopicModel
from app.infrastructure.db.models.topic_mention import TopicMentionModel
from app.infrastructure.db.models.trend_snapshot import TrendSnapshotModel


class SqlAlchemyTrendMetricsRepository(TrendMetricsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def topic_metrics(self) -> list[TopicMetrics]:
        # Effective timestamp: original publication time, falling back to ingest time.
        effective_ts = func.coalesce(
            SourceModel.source_created_at, SourceModel.created_at
        )
        stmt = (
            select(
                TopicModel.id,
                TopicModel.canonical_name,
                func.count(TopicMentionModel.id).label("mention_count"),
                func.coalesce(func.sum(SourceModel.score), 0).label("engagement_score"),
                func.count(func.distinct(SourceModel.platform)).label("platform_count"),
                func.max(effective_ts).label("latest_source_at"),
            )
            .join(TopicMentionModel, TopicMentionModel.topic_id == TopicModel.id)
            .join(SourceModel, SourceModel.id == TopicMentionModel.source_id)
            .where(TopicModel.is_active.is_(True))
            .group_by(TopicModel.id, TopicModel.canonical_name)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            TopicMetrics(
                topic_id=row.id,
                canonical_name=row.canonical_name,
                mention_count=int(row.mention_count),
                engagement_score=float(row.engagement_score),
                platform_count=int(row.platform_count),
                latest_source_at=row.latest_source_at,
            )
            for row in rows
        ]

    async def top_trends(self, limit: int = 20) -> list[TrendRanking]:
        latest_date = (
            await self._session.execute(func.max(TrendSnapshotModel.snapshot_date))
        ).scalar_one_or_none()
        if latest_date is None:
            return []

        stmt = (
            select(
                TopicModel.canonical_name,
                TrendSnapshotModel.mention_count,
                TrendSnapshotModel.engagement_score,
                TrendSnapshotModel.trend_score,
                TrendSnapshotModel.snapshot_date,
            )
            .join(TopicModel, TopicModel.id == TrendSnapshotModel.topic_id)
            .where(
                TrendSnapshotModel.snapshot_date == latest_date,
                TopicModel.is_active.is_(True),
            )
            .order_by(TrendSnapshotModel.trend_score.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            TrendRanking(
                canonical_name=row.canonical_name,
                mention_count=int(row.mention_count),
                engagement_score=float(row.engagement_score),
                trend_score=float(row.trend_score),
                snapshot_date=row.snapshot_date,
            )
            for row in rows
        ]
