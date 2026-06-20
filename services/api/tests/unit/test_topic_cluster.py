"""Unit tests for TopicClusterService (no ML, no database).

A fake topic repository computes cosine distance in Python so we can exercise
the clustering and canonical-selection logic deterministically.
"""

from __future__ import annotations

import math
from dataclasses import replace
from uuid import UUID, uuid4

from app.application.ports.embedding import EmbeddingPort
from app.application.use_cases.topics.topic_cluster_service import TopicClusterService
from app.domain.entities.topic import Topic
from app.domain.entities.topic_mention import TopicMention
from app.domain.repositories.topic_mention_repository import TopicMentionRepository
from app.domain.repositories.topic_repository import TopicRepository


def _cosine_distance(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 1.0
    return 1.0 - dot / (na * nb)


class FakeEmbedder(EmbeddingPort):
    @property
    def dimension(self) -> int:
        return 3

    def embed_texts(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover
        return [[0.0, 0.0, 0.0] for _ in texts]


class InMemoryTopicRepository(TopicRepository):
    def __init__(self, topics: list[Topic]) -> None:
        self._topics = {t.id: t for t in topics}

    async def add(self, topic: Topic) -> Topic:  # pragma: no cover
        raise NotImplementedError

    async def get_by_id(self, topic_id: UUID) -> Topic | None:  # pragma: no cover
        return self._topics.get(topic_id)

    async def get_by_canonical_name(self, canonical_name: str):  # type: ignore[no-untyped-def]
        return next((t for t in self._topics.values() if t.canonical_name == canonical_name), None)

    async def search_similar(self, embedding, limit: int = 10):  # type: ignore[no-untyped-def]
        return []

    async def list_all(self, limit: int = 1000, offset: int = 0):  # type: ignore[no-untyped-def]
        return list(self._topics.values())

    async def list_missing_embeddings(self, limit: int = 1000):  # type: ignore[no-untyped-def]
        return [t for t in self._topics.values() if t.embedding is None]

    async def list_with_embeddings(self, limit: int = 5000):  # type: ignore[no-untyped-def]
        return [t for t in self._topics.values() if t.embedding is not None]

    async def update_embedding(self, topic_id, embedding):  # type: ignore[no-untyped-def]
        self._topics[topic_id] = replace(self._topics[topic_id], embedding=embedding)

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

    async def add(self, mention: TopicMention):  # pragma: no cover  # type: ignore[no-untyped-def]
        raise NotImplementedError

    async def list_for_topic(self, topic_id, limit=100, offset=0):  # type: ignore[no-untyped-def]
        return []

    async def list_for_source(self, source_id):  # type: ignore[no-untyped-def]
        return []

    async def count_by_topic(self):  # type: ignore[no-untyped-def]
        return self._counts


def _topic(name: str, vec: list[float]) -> Topic:
    return Topic(canonical_name=name, embedding=vec, id=uuid4())


async def test_clusters_similar_topics_and_picks_canonical_by_mentions() -> None:
    # Two near-identical vectors (a cluster) + one unrelated topic (singleton).
    openai = _topic("OpenAI", [1.0, 0.0, 0.0])
    open_ai = _topic("Open AI Inc", [0.99, 0.01, 0.0])
    rust = _topic("Rust", [0.0, 1.0, 0.0])

    repo = InMemoryTopicRepository([openai, open_ai, rust])
    # "Open AI Inc" has more mentions, so it should be chosen as canonical.
    mentions = FakeMentionRepository({openai.id: 1, open_ai.id: 5, rust.id: 2})
    service = TopicClusterService(
        FakeEmbedder(), repo, mentions, similarity_threshold=0.9
    )

    report = await service.run()

    assert report.topics_total == 3
    assert report.cluster_count == 1  # only the OpenAI pair clusters
    assert report.duplicate_topics == 1
    cluster = report.clusters[0]
    assert cluster.size == 2
    assert cluster.canonical == "Open AI Inc"  # most mentions wins
    assert set(cluster.members) == {"OpenAI", "Open AI Inc"}


async def test_backfills_missing_embeddings() -> None:
    t = Topic(canonical_name="Solo", embedding=None, id=uuid4())
    repo = InMemoryTopicRepository([t])
    service = TopicClusterService(
        FakeEmbedder(), repo, FakeMentionRepository({}), similarity_threshold=0.9
    )

    report = await service.run()

    assert report.topics_embedded == 1
    assert report.cluster_count == 0  # a single topic is not a cluster
