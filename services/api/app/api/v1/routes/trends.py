"""Trend endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.dependencies import (
    SessionDep,
    TrendMetricsRepositoryDep,
    TrendScoringServiceDep,
)
from app.api.v1.schemas.trends import TrendRankingItem, TrendScoringResponse

router = APIRouter()


@router.post(
    "/score",
    response_model=TrendScoringResponse,
    summary="Generate daily trend scores and snapshots",
)
async def score_trends(
    service: TrendScoringServiceDep,
    session: SessionDep,
) -> TrendScoringResponse:
    """Score all topics and upsert today's TrendSnapshot rows.

    The route is the unit-of-work boundary: it commits on success; the session
    dependency rolls back on error.
    """
    result = await service.run()
    await session.commit()
    return TrendScoringResponse(
        topics_scored=result.topics_scored,
        snapshots_written=result.snapshots_written,
        snapshot_date=result.snapshot_date,
    )


@router.get(
    "",
    response_model=list[TrendRankingItem],
    summary="Ranked topics by trend score (latest snapshot)",
)
async def list_trends(
    metrics: TrendMetricsRepositoryDep,
    limit: int = Query(default=20, ge=1, le=200),
) -> list[TrendRankingItem]:
    """Return the top topics from the most recent snapshot date, by trend score."""
    rankings = await metrics.top_trends(limit=limit)
    return [
        TrendRankingItem(
            topic=r.canonical_name,
            mention_count=r.mention_count,
            engagement_score=r.engagement_score,
            trend_score=r.trend_score,
        )
        for r in rankings
    ]
