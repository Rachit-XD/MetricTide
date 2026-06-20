"""Topic endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.dependencies import (
    SessionDep,
    TopicClusterServiceDep,
    TopicExtractionServiceDep,
)
from app.api.v1.schemas.topics import (
    ProposedClusterSchema,
    TopicClusterResponse,
    TopicExtractionResponse,
)

router = APIRouter()


@router.post(
    "/extract",
    response_model=TopicExtractionResponse,
    summary="Extract topics from stored sources",
)
async def extract_topics(
    service: TopicExtractionServiceDep,
    session: SessionDep,
) -> TopicExtractionResponse:
    """Run topic extraction over stored sources, creating topics and mentions.

    The route is the unit-of-work boundary: it commits on success; the session
    dependency rolls back on error.
    """
    result = await service.run()
    await session.commit()
    return TopicExtractionResponse(
        sources_processed=result.sources_processed,
        topics_created=result.topics_created,
        mentions_created=result.mentions_created,
    )


@router.post(
    "/cluster",
    response_model=TopicClusterResponse,
    summary="Propose semantic topic clusters (recommendations only)",
)
async def cluster_topics(
    service: TopicClusterServiceDep,
    session: SessionDep,
    examples: int = Query(default=50, ge=1, le=500, description="Max clusters to return."),
) -> TopicClusterResponse:
    """Embed topics and propose canonical clusters by cosine similarity.

    Writes embeddings (committed here) but performs NO merges — the returned
    clusters are recommendations for review.
    """
    report = await service.run()
    await session.commit()
    return TopicClusterResponse(
        topics_embedded=report.topics_embedded,
        topics_total=report.topics_total,
        cluster_count=report.cluster_count,
        duplicate_topics=report.duplicate_topics,
        clusters=[
            ProposedClusterSchema(canonical=c.canonical, members=c.members, size=c.size)
            for c in report.clusters[:examples]
        ],
    )
