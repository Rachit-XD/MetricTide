"""Unit tests for deterministic trend scoring (no database)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from app.application.use_cases.trends.trend_score_calculator import (
    ScoreWeights,
    ScoringContext,
    TrendScoreCalculator,
)
from app.application.use_cases.trends.trend_scoring_service import TrendScoringService
from app.domain.entities.trend_snapshot import TrendSnapshot
from app.domain.repositories.trend_metrics_repository import (
    TopicMetrics,
    TrendMetricsRepository,
    TrendRanking,
)
from app.domain.repositories.trend_snapshot_repository import TrendSnapshotRepository

NOW = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)


def _ctx(**overrides) -> ScoringContext:  # type: ignore[no-untyped-def]
    base = {
        "max_mention_count": 10,
        "max_engagement": 1000.0,
        "max_platforms": 2,
        "reference_time": NOW,
        "recency_half_life_hours": 72.0,
    }
    base.update(overrides)
    return ScoringContext(**base)  # type: ignore[arg-type]


def _metrics(**overrides) -> TopicMetrics:  # type: ignore[no-untyped-def]
    base = {
        "topic_id": uuid4(),
        "canonical_name": "X",
        "mention_count": 5,
        "engagement_score": 500.0,
        "platform_count": 1,
        "latest_source_at": NOW,
    }
    base.update(overrides)
    return TopicMetrics(**base)  # type: ignore[arg-type]


# ---- Calculator ----


def test_score_is_bounded_and_max_metrics_score_high() -> None:
    calc = TrendScoreCalculator()
    top = _metrics(
        mention_count=10, engagement_score=1000.0, platform_count=2, latest_source_at=NOW
    )
    score = calc.score(top, _ctx())
    assert 0.0 <= score <= 100.0
    assert score > 99.0  # everything maxed -> near 100


def test_more_mentions_scores_higher() -> None:
    calc = TrendScoreCalculator()
    low = calc.score(_metrics(mention_count=1), _ctx())
    high = calc.score(_metrics(mention_count=10), _ctx())
    assert high > low


def test_older_sources_score_lower() -> None:
    calc = TrendScoreCalculator()
    fresh = calc.score(_metrics(latest_source_at=NOW), _ctx())
    stale = calc.score(_metrics(latest_source_at=NOW - timedelta(days=30)), _ctx())
    assert fresh > stale


def test_weights_not_summing_to_one_stay_bounded() -> None:
    calc = TrendScoreCalculator(ScoreWeights(2, 2, 2, 2))
    score = calc.score(
        _metrics(mention_count=10, engagement_score=1000.0, platform_count=2), _ctx()
    )
    assert 0.0 <= score <= 100.0


# ---- Service ----


class FakeMetricsRepository(TrendMetricsRepository):
    def __init__(self, metrics: list[TopicMetrics]) -> None:
        self._metrics = metrics

    async def topic_metrics(self) -> list[TopicMetrics]:
        return self._metrics

    async def top_trends(self, limit: int = 20) -> list[TrendRanking]:  # pragma: no cover
        return []


class FakeSnapshotRepository(TrendSnapshotRepository):
    def __init__(self, previous: dict[UUID, TrendSnapshot] | None = None) -> None:
        self.upserts: list[TrendSnapshot] = []
        self._previous = previous or {}

    async def add(self, snapshot: TrendSnapshot) -> TrendSnapshot:  # pragma: no cover
        raise NotImplementedError

    async def get_for_topic_on_date(self, topic_id, snapshot_date):  # type: ignore[no-untyped-def]
        return None

    async def list_top_for_date(self, snapshot_date, limit=20):  # type: ignore[no-untyped-def]
        return []

    async def upsert(self, snapshot: TrendSnapshot) -> None:
        self.upserts.append(snapshot)

    async def get_latest_before(self, topic_id, before_date):  # type: ignore[no-untyped-def]
        return self._previous.get(topic_id)


async def test_service_writes_one_snapshot_per_topic() -> None:
    metrics = [_metrics(mention_count=3), _metrics(mention_count=7)]
    snap_repo = FakeSnapshotRepository()
    service = TrendScoringService(
        FakeMetricsRepository(metrics), snap_repo, TrendScoreCalculator()
    )

    result = await service.run(snapshot_date=date(2026, 6, 20))

    assert result.topics_scored == 2
    assert result.snapshots_written == 2
    assert len(snap_repo.upserts) == 2
    assert all(0.0 <= s.trend_score <= 100.0 for s in snap_repo.upserts)


async def test_service_computes_growth_from_previous_snapshot() -> None:
    topic = _metrics(mention_count=10)
    previous = TrendSnapshot(
        topic_id=topic.topic_id,
        snapshot_date=date(2026, 6, 19),
        mention_count=5,
        engagement_score=0.0,
        growth_rate=0.0,
        trend_score=0.0,
    )
    snap_repo = FakeSnapshotRepository(previous={topic.topic_id: previous})
    service = TrendScoringService(
        FakeMetricsRepository([topic]), snap_repo, TrendScoreCalculator()
    )

    await service.run(snapshot_date=date(2026, 6, 20))

    # (10 - 5) / 5 = 1.0
    assert snap_repo.upserts[0].growth_rate == 1.0
