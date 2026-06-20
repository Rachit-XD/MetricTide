"""Topic endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.dependencies import (
    CanonicalTopicServiceDep,
    SessionDep,
    SettingsDep,
    TopicClusterServiceDep,
    TopicExtractionServiceDep,
)
from app.api.v1.schemas.topics import (
    MergeClusterSchema,
    MergeMemberSchema,
    MergeReportResponse,
    ProposedClusterSchema,
    TopicClusterResponse,
    TopicClustersResponse,
    TopicExtractionResponse,
)
from app.application.use_cases.topics.canonical_topic_service import (
    MergeCluster,
    MergeReport,
)

router = APIRouter()


def _cluster_to_schema(cluster: MergeCluster) -> MergeClusterSchema:
    return MergeClusterSchema(
        canonical=cluster.canonical.canonical_name,
        canonical_mentions=cluster.canonical_mentions,
        min_similarity=round(cluster.min_similarity, 4),
        members=[
            MergeMemberSchema(
                name=m.topic.canonical_name,
                mention_count=m.mention_count,
                similarity=m.similarity,
            )
            for m in cluster.members
        ],
    )


def _report_to_schema(report: MergeReport) -> MergeReportResponse:
    return MergeReportResponse(
        mode=report.mode,
        cluster_count=len(report.clusters),
        topics_merged=report.topics_merged,
        mentions_repointed=report.mentions_repointed,
        mentions_deduped=report.mentions_deduped,
        clusters=[_cluster_to_schema(c) for c in report.clusters],
    )


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


@router.get(
    "/clusters",
    response_model=TopicClustersResponse,
    summary="List candidate merge clusters (read-only)",
)
async def list_clusters(
    service: CanonicalTopicServiceDep,
    settings: SettingsDep,
) -> TopicClustersResponse:
    """Candidate clusters at the broad discovery threshold, for review."""
    clusters = await service.list_candidate_clusters(
        settings.cluster_similarity_threshold
    )
    return TopicClustersResponse(
        cluster_count=len(clusters),
        clusters=[_cluster_to_schema(c) for c in clusters],
    )


@router.post(
    "/merge-preview",
    response_model=MergeReportResponse,
    summary="Dry-run topic merge (no writes)",
)
async def merge_preview(service: CanonicalTopicServiceDep) -> MergeReportResponse:
    """Show the merge plan at the strict merge threshold without applying it."""
    return _report_to_schema(await service.preview())


@router.post(
    "/merge-apply",
    response_model=MergeReportResponse,
    summary="Apply topic merges (destructive: repoints mentions, deactivates topics)",
)
async def merge_apply(
    service: CanonicalTopicServiceDep,
    session: SessionDep,
) -> MergeReportResponse:
    """Apply the merge plan: repoint mentions, record aliases, deactivate merged topics.

    Commits on success; the session dependency rolls back on error.
    """
    report = await service.apply()
    await session.commit()
    return _report_to_schema(report)
