"""Pydantic schemas for TopicMention."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TopicMentionCreate(BaseModel):
    source_id: UUID
    topic_id: UUID
    confidence_score: float = Field(ge=0.0, le=1.0)


class TopicMentionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    topic_id: UUID
    confidence_score: float
    created_at: datetime
