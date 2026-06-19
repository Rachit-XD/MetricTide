"""Unit tests for ingestion (no database, no network).

Covers the platform-agnostic dedup/persist core (SourceIngestionService) and
both runners (Reddit, Hacker News) including failure isolation.
"""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID, uuid4

from app.application.ports.hackernews_client import (
    HackerNewsClientPort,
    HackerNewsStory,
)
from app.application.ports.reddit_client import RedditClientPort, RedditPost
from app.application.use_cases.ingestion.hackernews import HackerNewsIngestionRunner
from app.application.use_cases.ingestion.reddit import RedditIngestionRunner
from app.application.use_cases.ingestion.source_ingestion_service import (
    SourceIngestionService,
)
from app.domain.entities.platform import Platform
from app.domain.entities.source import Source
from app.domain.repositories.source_repository import SourceRepository


class FakeSourceRepository(SourceRepository):
    """In-memory repository keyed by (platform, external_id)."""

    def __init__(self, existing: list[Source] | None = None) -> None:
        self._store: dict[tuple[Platform, str], Source] = {}
        for src in existing or []:
            self._store[(src.platform, src.external_id)] = src

    async def add(self, source: Source) -> Source:
        stored = replace(source, id=uuid4())
        self._store[(source.platform, source.external_id)] = stored
        return stored

    async def get_by_id(self, source_id: UUID) -> Source | None:
        return next((s for s in self._store.values() if s.id == source_id), None)

    async def get_by_external_id(
        self, platform: Platform, external_id: str
    ) -> Source | None:
        return self._store.get((platform, external_id))

    async def list_recent(self, limit: int = 100, offset: int = 0) -> list[Source]:
        return list(self._store.values())[offset : offset + limit]


class FakeRedditClient(RedditClientPort):
    def __init__(
        self,
        posts_by_subreddit: dict[str, list[RedditPost]],
        failing: set[str] | None = None,
    ) -> None:
        self._posts = posts_by_subreddit
        self._failing = failing or set()

    async def fetch_new(self, subreddit: str, limit: int = 100) -> list[RedditPost]:
        if subreddit in self._failing:
            raise RuntimeError("boom")
        return self._posts.get(subreddit, [])


class FakeHackerNewsClient(HackerNewsClientPort):
    def __init__(self, stories: list[HackerNewsStory], fail: bool = False) -> None:
        self._stories = stories
        self._fail = fail

    async def fetch_top_stories(self, limit: int = 50) -> list[HackerNewsStory]:
        if self._fail:
            raise RuntimeError("listing unavailable")
        return self._stories[:limit]


def _reddit_post(external_id: str, subreddit: str) -> RedditPost:
    return RedditPost(external_id=external_id, subreddit=subreddit, title=f"r-{external_id}")


def _source(platform: Platform, external_id: str) -> Source:
    return Source(platform=platform, external_id=external_id, title=f"t-{external_id}")


# ---- SourceIngestionService.ingest ----


async def test_ingest_inserts_new_and_counts() -> None:
    repo = FakeSourceRepository()
    service = SourceIngestionService(repo)

    result = await service.ingest(
        [_source(Platform.HACKERNEWS, "1"), _source(Platform.HACKERNEWS, "2")]
    )

    assert (result.fetched, result.inserted, result.skipped) == (2, 2, 0)


async def test_ingest_skips_existing_and_in_batch_duplicates() -> None:
    repo = FakeSourceRepository(existing=[_source(Platform.REDDIT, "a")])
    service = SourceIngestionService(repo)

    result = await service.ingest(
        [
            _source(Platform.REDDIT, "a"),  # already stored -> skip
            _source(Platform.REDDIT, "b"),
            _source(Platform.REDDIT, "b"),  # in-batch dup -> skip
        ]
    )

    assert (result.fetched, result.inserted, result.skipped) == (3, 1, 2)


async def test_ingest_dedup_is_per_platform() -> None:
    repo = FakeSourceRepository()
    service = SourceIngestionService(repo)

    # Same external_id on different platforms must both insert.
    result = await service.ingest(
        [_source(Platform.REDDIT, "x"), _source(Platform.HACKERNEWS, "x")]
    )

    assert (result.fetched, result.inserted, result.skipped) == (2, 2, 0)


# ---- RedditIngestionRunner ----


async def test_reddit_runner_isolates_failing_subreddit() -> None:
    client = FakeRedditClient(
        {"programming": [_reddit_post("a", "programming")], "artificial": []},
        failing={"artificial"},
    )
    repo = FakeSourceRepository()
    runner = RedditIngestionRunner(
        client, SourceIngestionService(repo), ["artificial", "programming"]
    )

    result = await runner.run()

    assert (result.fetched, result.inserted, result.skipped) == (1, 1, 0)


# ---- HackerNewsIngestionRunner ----


async def test_hackernews_runner_maps_and_inserts() -> None:
    stories = [
        HackerNewsStory(id=1, title="A", url="http://a", score=10, by="alice", time=1),
        HackerNewsStory(id=2, title="B", url=None, score=5, by="bob", time=2),
    ]
    repo = FakeSourceRepository()
    runner = HackerNewsIngestionRunner(
        FakeHackerNewsClient(stories), SourceIngestionService(repo)
    )

    result = await runner.run()

    assert (result.fetched, result.inserted, result.skipped) == (2, 2, 0)
    stored = await repo.get_by_external_id(Platform.HACKERNEWS, "1")
    assert stored is not None
    assert stored.author == "alice"
    assert stored.platform is Platform.HACKERNEWS


async def test_hackernews_runner_isolates_listing_failure() -> None:
    repo = FakeSourceRepository()
    runner = HackerNewsIngestionRunner(
        FakeHackerNewsClient([], fail=True), SourceIngestionService(repo)
    )

    result = await runner.run()

    assert (result.fetched, result.inserted, result.skipped) == (0, 0, 0)
