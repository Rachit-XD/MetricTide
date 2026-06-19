"""Schemas for ingestion endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class IngestionRunResponse(BaseModel):
    """Result of an ingestion run."""

    fetched: int = Field(description="Total posts fetched across all subreddits.")
    inserted: int = Field(description="New sources persisted.")
    skipped: int = Field(description="Posts skipped as duplicates.")
