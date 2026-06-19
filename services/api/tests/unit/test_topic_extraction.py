"""Unit tests for topic extraction (no ML models, no database)."""

from __future__ import annotations

from uuid import UUID, uuid4

from app.application.ports.topic_extraction import ExtractedTopic, TopicExtractionPort
from app.application.use_cases.topics.normalizer import TopicNormalizer
from app.application.use_cases.topics.topic_extraction_service import (
    TopicExtractionService,
)
from app.domain.entities.platform import Platform
from app.domain.entities.source import Source
from app.domain.entities.topic import Topic
from app.domain.entities.topic_mention import TopicMention
from app.domain.repositories.source_repository import SourceRepository
from app.domain.repositories.topic_mention_repository import TopicMentionRepository
from app.domain.repositories.topic_repository import TopicRepository


# ---- Normalizer ----


def test_normalizer_applies_aliases() -> None:
    n = TopicNormalizer()
    assert n.normalize("Open AI") == "OpenAI"
    assert n.normalize("  large   language models ") == "LLM"
    assert n.normalize("LLM") == "LLM"


def test_normalizer_drops_noise() -> None:
    n = TopicNormalizer()
    assert n.normalize("a") is None
    assert n.normalize("Show HN") is None
    assert n.normalize("2026") is None


# ---- Fakes ----


class FakeExtractor(TopicExtractionPort):
    def __init__(self, by_text: dict[str, list[ExtractedTopic]]) -> None:
        self._by_text = by_text

    def extract(self, text: str) -> list[ExtractedTopic]:
        return self._by_text.get(text, [])


class FakeSourceRepository(SourceRepository):
    def __init__(self, sources: list[Source]) -> None:
        self._sources = sources

    async def add(self, source: Source) -> Source:  # pragma: no cover
        raise NotImplementedError

    async def get_by_id(self, source_id: UUID) -> Source | None:  # pragma: no cover
        return None

    async def get_by_external_id(self, platform: Platform, external_id: str):  # type: ignore[no-untyped-def]
        return None

    async def list_recent(self, limit: int = 100, offset: int = 0) -> list[Source]:
        return self._sources[offset : offset + limit]


class FakeTopicRepository(TopicRepository):
    def __init__(self, existing: list[Topic] | None = None) -> None:
        self._by_name: dict[str, Topic] = {}
        for t in existing or []:
            self._by_name[t.canonical_name] = t

    async def add(self, topic: Topic) -> Topic:
        from dataclasses import replace

        stored = replace(topic, id=uuid4())
        self._by_name[topic.canonical_name] = stored
        return stored

    async def get_by_id(self, topic_id: UUID) -> Topic | None:  # pragma: no cover
        return next((t for t in self._by_name.values() if t.id == topic_id), None)

    async def get_by_canonical_name(self, canonical_name: str) -> Topic | None:
        return self._by_name.get(canonical_name)

    async def search_similar(self, embedding, limit: int = 10):  # type: ignore[no-untyped-def]
        return []


class FakeMentionRepository(TopicMentionRepository):
    def __init__(self) -> None:
        self.items: list[TopicMention] = []

    async def add(self, mention: TopicMention) -> TopicMention:
        from dataclasses import replace

        stored = replace(mention, id=uuid4())
        self.items.append(stored)
        return stored

    async def list_for_topic(self, topic_id, limit=100, offset=0):  # type: ignore[no-untyped-def]
        return [m for m in self.items if m.topic_id == topic_id]

    async def list_for_source(self, source_id):  # type: ignore[no-untyped-def]
        return [m for m in self.items if m.source_id == source_id]


def _source(external_id: str, title: str) -> Source:
    return Source(platform=Platform.HACKERNEWS, external_id=external_id, title=title, id=uuid4())


# ---- Service ----


async def test_extracts_creates_topics_and_mentions() -> None:
    src = _source("1", "Noam Shazeer Joins OpenAI")
    extractor = FakeExtractor(
        {
            "Noam Shazeer Joins OpenAI": [
                ExtractedTopic("Open AI", 0.8),  # -> OpenAI
                ExtractedTopic("Noam Shazeer", 0.8),
                ExtractedTopic("ai", 0.5),  # -> AI
                ExtractedTopic("the", 0.9),  # dropped by normalizer
            ]
        }
    )
    topics = FakeTopicRepository()
    mentions = FakeMentionRepository()
    service = TopicExtractionService(
        extractor, TopicNormalizer(), FakeSourceRepository([src]), topics, mentions
    )

    result = await service.run()

    assert result.sources_processed == 1
    assert result.topics_created == 3  # OpenAI, Noam Shazeer, AI
    assert result.mentions_created == 3
    assert await topics.get_by_canonical_name("OpenAI") is not None


async def test_reuses_existing_topic_and_is_idempotent() -> None:
    src = _source("1", "About OpenAI")
    extractor = FakeExtractor({"About OpenAI": [ExtractedTopic("OpenAI", 0.9)]})
    topics = FakeTopicRepository(existing=[Topic(canonical_name="OpenAI", id=uuid4())])
    mentions = FakeMentionRepository()
    service = TopicExtractionService(
        extractor, TopicNormalizer(), FakeSourceRepository([src]), topics, mentions
    )

    first = await service.run()
    assert (first.topics_created, first.mentions_created) == (0, 1)  # topic reused

    second = await service.run()
    assert (second.topics_created, second.mentions_created) == (0, 0)  # mention deduped


async def test_min_confidence_filters_weak_candidates() -> None:
    src = _source("1", "Some Title")
    extractor = FakeExtractor(
        {"Some Title": [ExtractedTopic("Python", 0.2), ExtractedTopic("Rust", 0.9)]}
    )
    topics = FakeTopicRepository()
    mentions = FakeMentionRepository()
    service = TopicExtractionService(
        extractor,
        TopicNormalizer(),
        FakeSourceRepository([src]),
        topics,
        mentions,
        min_confidence=0.3,
    )

    result = await service.run()

    assert result.topics_created == 1  # only Rust passes the threshold
    assert await topics.get_by_canonical_name("Rust") is not None
    assert await topics.get_by_canonical_name("Python") is None
