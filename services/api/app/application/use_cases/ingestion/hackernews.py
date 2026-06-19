"""Hacker News ingestion runner: fetch top stories, map to Source, ingest.

A failure fetching the story listing is isolated (logged, empty run) so the
endpoint still returns a clean result.
"""

from __future__ import annotations

from app.application.ports.hackernews_client import (
    HackerNewsClientPort,
    HackerNewsStory,
)
from app.application.use_cases.ingestion.source_ingestion_service import (
    IngestionResult,
    SourceIngestionService,
)
from app.core.logging import get_logger
from app.core.timeutils import epoch_to_utc
from app.domain.entities.platform import Platform
from app.domain.entities.source import Source

logger = get_logger(__name__)


class HackerNewsIngestionRunner:
    def __init__(
        self,
        hackernews_client: HackerNewsClientPort,
        ingestion_service: SourceIngestionService,
        fetch_limit: int = 50,
    ) -> None:
        self._hackernews = hackernews_client
        self._service = ingestion_service
        self._fetch_limit = fetch_limit

    async def run(self) -> IngestionResult:
        try:
            stories = await self._hackernews.fetch_top_stories(self._fetch_limit)
        except Exception:
            logger.warning("ingestion.fetch_failed", source="hackernews", exc_info=True)
            stories = []
        candidates = [self._to_source(story) for story in stories]
        return await self._service.ingest(candidates)

    @staticmethod
    def _to_source(story: HackerNewsStory) -> Source:
        return Source(
            platform=Platform.HACKERNEWS,
            external_id=str(story.id),
            title=story.title,
            content=None,
            author=story.by,
            score=story.score,
            url=story.url,
            source_created_at=epoch_to_utc(story.time),
        )
