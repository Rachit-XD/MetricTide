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


# ---- Canonical consolidation (Phase 8) ----


class MergeMemberSchema(BaseModel):
    name: str
    mention_count: int
    similarity: float


class MergeClusterSchema(BaseModel):
    canonical: str
    canonical_mentions: int
    min_similarity: float
    members: list[MergeMemberSchema]


class TopicClustersResponse(BaseModel):
    """Candidate clusters for review (read-only)."""

    cluster_count: int
    clusters: list[MergeClusterSchema]


class MergeReportResponse(BaseModel):
    """Outcome of a merge preview (dry-run) or apply."""

    mode: str = Field(description='"preview" (no writes) or "apply".')
    cluster_count: int
    topics_merged: int = Field(description="Topics that would be / were merged away.")
    mentions_repointed: int = Field(description="Mentions moved to canonical (apply only).")
    mentions_deduped: int = Field(description="Duplicate mentions dropped (apply only).")
    clusters: list[MergeClusterSchema]
