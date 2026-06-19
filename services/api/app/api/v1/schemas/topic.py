"""Pydantic schemas for Topic."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TopicCreate(BaseModel):
    canonical_name: str = Field(max_length=255)
    description: str | None = None
    embedding: list[float] | None = None


class TopicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    canonical_name: str
    description: str | None
    created_at: datetime
    # `embedding` is intentionally omitted from the default read schema: it is
    # large and primarily an internal clustering artifact. Expose via a
    # dedicated schema if a consumer ever needs it.
