"""Topic endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import SessionDep, TopicExtractionServiceDep
from app.api.v1.schemas.topics import TopicExtractionResponse

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
