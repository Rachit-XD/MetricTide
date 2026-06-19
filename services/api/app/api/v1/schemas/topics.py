"""Schemas for topic endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TopicExtractionResponse(BaseModel):
    """Result of a topic-extraction run."""

    sources_processed: int = Field(description="Sources read and analyzed.")
    topics_created: int = Field(description="New topics created.")
    mentions_created: int = Field(description="New (source, topic) mentions created.")
