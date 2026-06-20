"""Schemas for topic endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TopicExtractionResponse(BaseModel):
    """Result of a topic-extraction run."""

    sources_processed: int = Field(description="Sources read and analyzed.")
    topics_created: int = Field(description="New topics created.")
    mentions_created: int = Field(description="New (source, topic) mentions created.")


class ProposedClusterSchema(BaseModel):
    """A proposed group of similar topics (recommendation only)."""

    canonical: str = Field(description="Proposed canonical topic name.")
    members: list[str] = Field(description="Topics in the cluster (canonical first).")
    size: int = Field(description="Number of topics in the cluster.")


class TopicClusterResponse(BaseModel):
    """Result of a semantic consolidation run (recommendations only)."""

    topics_embedded: int = Field(description="Embeddings generated this run.")
    topics_total: int = Field(description="Topics with embeddings considered.")
    cluster_count: int = Field(description="Number of multi-topic clusters found.")
    duplicate_topics: int = Field(description="Topics that would be merged away.")
    clusters: list[ProposedClusterSchema] = Field(
        description="Example proposed clusters (no merges performed)."
    )
