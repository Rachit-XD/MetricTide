"""Trend scoring use case: compute scores and write daily TrendSnapshots.

For the snapshot date (default: today, UTC), aggregate per-topic metrics, score
each topic deterministically, compute growth vs. the previous snapshot, and
upsert one TrendSnapshot per topic. Idempotent per day.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from app.application.use_cases.trends.trend_score_calculator import (
    ScoringContext,
    TrendScoreCalculator,
)
from app.core.logging import get_logger
from app.domain.entities.trend_snapshot import TrendSnapshot
from app.domain.repositories.trend_metrics_repository import (
    TopicMetrics,
    TrendMetricsRepository,
)
from app.domain.repositories.trend_snapshot_repository import TrendSnapshotRepository

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class TrendScoringResult:
    topics_scored: int
    snapshots_written: int
    snapshot_date: date


class TrendScoringService:
    def __init__(
        self,
        metrics_repository: TrendMetricsRepository,
        snapshot_repository: TrendSnapshotRepository,
        calculator: TrendScoreCalculator,
        recency_half_life_hours: float = 72.0,
    ) -> None:
        self._metrics = metrics_repository
        self._snapshots = snapshot_repository
        self._calculator = calculator
        self._recency_half_life_hours = recency_half_life_hours

    async def run(self, snapshot_date: date | None = None) -> TrendScoringResult:
        now = datetime.now(UTC)
        target_date = snapshot_date or now.date()

        metrics = await self._metrics.topic_metrics()
        ctx = self._build_context(metrics, now)

        written = 0
        for topic in metrics:
            trend_score = self._calculator.score(topic, ctx)
            previous = await self._snapshots.get_latest_before(topic.topic_id, target_date)
            growth_rate = self._growth(topic.mention_count, previous)

            await self._snapshots.upsert(
                TrendSnapshot(
                    topic_id=topic.topic_id,
                    snapshot_date=target_date,
                    mention_count=topic.mention_count,
                    engagement_score=topic.engagement_score,
                    growth_rate=growth_rate,
                    trend_score=trend_score,
                )
            )
            written += 1

        logger.info(
            "trends.scoring_completed",
            topics_scored=len(metrics),
            snapshots_written=written,
            snapshot_date=target_date.isoformat(),
        )
        return TrendScoringResult(
            topics_scored=len(metrics),
            snapshots_written=written,
            snapshot_date=target_date,
        )

    def _build_context(
        self, metrics: list[TopicMetrics], reference_time: datetime
    ) -> ScoringContext:
        return ScoringContext(
            max_mention_count=max((m.mention_count for m in metrics), default=0),
            max_engagement=max((m.engagement_score for m in metrics), default=0.0),
            max_platforms=max((m.platform_count for m in metrics), default=0),
            reference_time=reference_time,
            recency_half_life_hours=self._recency_half_life_hours,
        )

    @staticmethod
    def _growth(current_mentions: int, previous: TrendSnapshot | None) -> float:
        if previous is None or previous.mention_count <= 0:
            return 0.0
        return (current_mentions - previous.mention_count) / previous.mention_count
