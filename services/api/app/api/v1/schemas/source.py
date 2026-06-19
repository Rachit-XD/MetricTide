"""Pydantic schemas for Source."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities.platform import Platform


class SourceCreate(BaseModel):
    platform: Platform
    external_id: str = Field(max_length=255)
    title: str
    content: str | None = None
    author: str | None = Field(default=None, max_length=255)
    score: int | None = None
    url: str | None = None


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    platform: Platform
    external_id: str
    title: str
    content: str | None
    author: str | None
    score: int | None
    url: str | None
    created_at: datetime
