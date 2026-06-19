"""Reddit ingestion runner: fetch latest posts, map to Source, ingest.

Per-subreddit fetch failures are isolated (logged, run continues) so one bad
fetch never aborts the whole run.
"""

from __future__ import annotations

from app.application.ports.reddit_client import RedditClientPort, RedditPost
from app.application.use_cases.ingestion.source_ingestion_service import (
    IngestionResult,
    SourceIngestionService,
)
from app.core.logging import get_logger
from app.core.timeutils import epoch_to_utc
from app.domain.entities.platform import Platform
from app.domain.entities.source import Source

logger = get_logger(__name__)


class RedditIngestionRunner:
    def __init__(
        self,
        reddit_client: RedditClientPort,
        ingestion_service: SourceIngestionService,
        subreddits: list[str],
        fetch_limit: int = 100,
    ) -> None:
        self._reddit = reddit_client
        self._service = ingestion_service
        self._subreddits = subreddits
        self._fetch_limit = fetch_limit

    async def run(self) -> IngestionResult:
        candidates: list[Source] = []
        for subreddit in self._subreddits:
            try:
                posts = await self._reddit.fetch_new(subreddit, self._fetch_limit)
            except Exception:
                logger.warning(
                    "ingestion.fetch_failed", source="reddit", subreddit=subreddit, exc_info=True
                )
                continue
            candidates.extend(self._to_source(post) for post in posts)
        return await self._service.ingest(candidates)

    @staticmethod
    def _to_source(post: RedditPost) -> Source:
        return Source(
            platform=Platform.REDDIT,
            external_id=post.external_id,
            title=post.title,
            content=post.content,
            author=post.author,
            score=post.score,
            url=post.url,
            source_created_at=epoch_to_utc(post.created_utc),
        )
