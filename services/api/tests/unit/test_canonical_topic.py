"""Unit tests for CanonicalTopicService (no database)."""

from __future__ import annotations

import math
from uuid import UUID, uuid4

from app.application.use_cases.topics.canonical_topic_service import (
    CanonicalTopicService,
)
from app.domain.entities.topic import Topic
from app.domain.repositories.topic_mention_repository import TopicMentionRepository
from app.domain.repositories.topic_merge_repository import (
    RepointResult,
    TopicMergeRepository,
)
from app.domain.repositories.topic_repository import TopicRepository


def _cosine_distance(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return 1.0 - dot / (na * nb)


class InMemoryTopicRepository(TopicRepository):
    def __init__(self, topics: list[Topic]) -> None:
        self._topics = {t.id: t for t in topics}

    async def add(self, topic: Topic) -> Topic:  # pragma: no cover
        raise NotImplementedError

    async def get_by_id(self, topic_id: UUID) -> Topic | None:  # pragma: no cover
        return self._topics.get(topic_id)

    async def get_by_canonical_name(self, canonical_name: str):  # type: ignore[no-untyped-def]
        return None

    async def search_similar(self, embedding, limit: int = 10):  # type: ignore[no-untyped-def]
        return []

    async def list_all(self, limit: int = 1000, offset: int = 0):  # type: ignore[no-untyped-def]
        return list(self._topics.values())

    async def list_missing_embeddings(self, limit: int = 1000):  # type: ignore[no-untyped-def]
        return []

    async def list_with_embeddings(self, limit: int = 5000):  # type: ignore[no-untyped-def]
        return [t for t in self._topics.values() if t.embedding is not None]

    async def update_embedding(self, topic_id, embedding):  # type: ignore[no-untyped-def]
        return None

    async def find_neighbors(self, embedding, exclude_id, max_distance, limit: int = 10):  # type: ignore[no-untyped-def]
        out = []
        for t in self._topics.values():
            if t.id == exclude_id or t.embedding is None:
                continue
            d = _cosine_distance(embedding, t.embedding)
            if d <= max_distance:
                out.append((t, d))
        out.sort(key=lambda x: x[1])
        return out[:limit]


class FakeMentionRepository(TopicMentionRepository):
    def __init__(self, counts: dict[UUID, int]) -> None:
        self._counts = counts

    async def add(self, mention):  # pragma: no cover  # type: ignore[no-untyped-def]
        raise NotImplementedError

    async def list_for_topic(self, topic_id, limit=100, offset=0):  # type: ignore[no-untyped-def]
        return []

    async def list_for_source(self, source_id):  # type: ignore[no-untyped-def]
        return []

    async def count_by_topic(self):  # type: ignore[no-untyped-def]
        return self._counts


class FakeMergeRepository(TopicMergeRepository):
    def __init__(self) -> None:
        self.repointed: list[tuple[UUID, UUID]] = []
        self.aliases: list[tuple[UUID, str]] = []
        self.deactivated: list[tuple[UUID, UUID]] = []

    async def repoint_mentions(self, from_topic_id, to_topic_id):  # type: ignore[no-untyped-def]
        self.repointed.append((from_topic_id, to_topic_id))
        return RepointResult(repointed=1, deduped=0)

    async def add_alias(self, canonical_id, alias):  # type: ignore[no-untyped-def]
        self.aliases.append((canonical_id, alias))

    async def deactivate_topic(self, topic_id, merged_into_id):  # type: ignore[no-untyped-def]
        self.deactivated.append((topic_id, merged_into_id))


def _topic(name: str, vec: list[float] | None = None) -> Topic:
    return Topic(canonical_name=name, embedding=vec, id=uuid4())


# ---- Canonical selection rules ----


def test_canonical_prefers_shorter_proper_name() -> None:
    counts: dict[UUID, int] = {}
    open_ai = _topic("Open AI")
    openai = _topic("OpenAI")
    chosen = CanonicalTopicService._choose_canonical([open_ai, openai], counts)
    assert chosen.canonical_name == "OpenAI"


def test_canonical_prefers_internal_capitalization() -> None:
    counts: dict[UUID, int] = {}
    lower = _topic("Clickhouse")
    proper = _topic("ClickHouse")
    chosen = CanonicalTopicService._choose_canonical([lower, proper], counts)
    assert chosen.canonical_name == "ClickHouse"


def test_canonical_prefers_properly_cased_over_lowercase() -> None:
    counts: dict[UUID, int] = {}
    lower = _topic("openai")
    proper = _topic("OpenAI")
    chosen = CanonicalTopicService._choose_canonical([lower, proper], counts)
    assert chosen.canonical_name == "OpenAI"


def test_canonical_mention_count_beats_length() -> None:
    a = _topic("ClickHouse")
    b = _topic("CH")
    counts = {a.id: 50, b.id: 1}
    # Both properly cased; higher mentions wins over shorter name.
    chosen = CanonicalTopicService._choose_canonical([a, b], counts)
    assert chosen.canonical_name == "ClickHouse"


# ---- apply ----


async def test_apply_merges_similar_cluster() -> None:
    canonical = _topic("OpenAI", [1.0, 0.0, 0.0])
    member = _topic("Open AI Inc", [0.99, 0.02, 0.0])
    unrelated = _topic("Rust", [0.0, 1.0, 0.0])
    repo = InMemoryTopicRepository([canonical, member, unrelated])
    counts = {canonical.id: 1, member.id: 3, unrelated.id: 2}
    merge = FakeMergeRepository()
    service = CanonicalTopicService(
        repo, FakeMentionRepository(counts), merge, similarity_threshold=0.9
    )

    report = await service.apply()

    assert report.mode == "apply"
    assert report.topics_merged == 1
    # member (more mentions) is canonical? No: both properly cased, member has
    # more mentions (3 > 1) -> member becomes canonical, OpenAI is merged in.
    assert merge.deactivated == [(canonical.id, member.id)]
    assert merge.aliases == [(member.id, "OpenAI")]
    assert report.mentions_repointed == 1
