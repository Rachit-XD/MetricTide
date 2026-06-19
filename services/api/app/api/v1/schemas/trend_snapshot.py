"""Pydantic schemas for TrendSnapshot."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TrendSnapshotCreate(BaseModel):
    topic_id: UUID
    snapshot_date: date
    mention_count: int = Field(ge=0)
    engagement_score: float
    growth_rate: float
    trend_score: float


class TrendSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    topic_id: UUID
    snapshot_date: date
    mention_count: int
    engagement_score: float
    growth_rate: float
    trend_score: float
    created_at: datetime
