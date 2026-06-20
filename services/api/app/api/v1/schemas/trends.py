"""Schemas for trend endpoints."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class TrendScoringResponse(BaseModel):
    """Result of a trend-scoring run."""

    topics_scored: int = Field(description="Topics scored.")
    snapshots_written: int = Field(description="TrendSnapshot rows upserted.")
    snapshot_date: date = Field(description="Date the snapshots were written for.")


class TrendRankingItem(BaseModel):
    """One ranked topic in the trends listing."""

    topic: str
    mention_count: int
    engagement_score: float
    trend_score: float
