"""Semantic topic consolidation (recommendations only).

Two steps:

1. **Backfill embeddings** for topics that don't have one (all-MiniLM-L6-v2).
2. **Cluster** topics by pgvector cosine similarity: build a graph linking topics
   whose distance is within a threshold, take connected components, and propose a
   canonical name per multi-topic cluster.

This NEVER merges topics or mutates mentions — it only writes embeddings and
returns a proposed mapping for human review.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from uuid import UUID

from app.application.ports.embedding import EmbeddingPort
from app.core.logging import get_logger
from app.domain.entities.topic import Topic
from app.domain.repositories.topic_mention_repository import TopicMentionRepository
from app.domain.repositories.topic_repository import TopicRepository

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ProposedCluster:
    """A group of similar topics with a proposed canonical name."""

    canonical: str
    members: list[str]

    @property
    def size(self) -> int:
        return len(self.members)


@dataclass(slots=True)
class TopicClusterReport:
    topics_embedded: int
    topics_total: int
    cluster_count: int  # number of multi-topic clusters
    duplicate_topics: int  # members that would be merged away (size - 1 per cluster)
    clusters: list[ProposedCluster] = field(default_factory=list)


class _UnionFind:
    def __init__(self) -> None:
        self._parent: dict[UUID, UUID] = {}

    def add(self, item: UUID) -> None:
        self._parent.setdefault(item, item)

    def find(self, item: UUID) -> UUID:
        root = item
        while self._parent[root] != root:
            root = self._parent[root]
        # Path compression.
        while self._parent[item] != root:
            self._parent[item], item = root, self._parent[item]
        return root

    def union(self, a: UUID, b: UUID) -> None:
        self.add(a)
        self.add(b)
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self._parent[ra] = rb

    def groups(self) -> dict[UUID, list[UUID]]:
        out: dict[UUID, list[UUID]] = {}
        for item in self._parent:
            out.setdefault(self.find(item), []).append(item)
        return out


class TopicClusterService:
    def __init__(
        self,
        embedder: EmbeddingPort,
        topic_repository: TopicRepository,
        mention_repository: TopicMentionRepository,
        similarity_threshold: float = 0.80,
        neighbor_limit: int = 10,
    ) -> None:
        self._embedder = embedder
        self._topics = topic_repository
        self._mentions = mention_repository
        # pgvector returns cosine *distance* = 1 - cosine_similarity.
        self._max_distance = 1.0 - similarity_threshold
        self._neighbor_limit = neighbor_limit

    async def run(self) -> TopicClusterReport:
        topics_embedded = await self._backfill_embeddings()
        topics = await self._topics.list_with_embeddings()
        clusters = await self._build_clusters(topics)

        multi = [c for c in clusters if c.size > 1]
        report = TopicClusterReport(
            topics_embedded=topics_embedded,
            topics_total=len(topics),
            cluster_count=len(multi),
            duplicate_topics=sum(c.size - 1 for c in multi),
            clusters=multi,
        )
        logger.info(
            "topics.cluster_completed",
            topics_embedded=topics_embedded,
            topics_total=report.topics_total,
            cluster_count=report.cluster_count,
            duplicate_topics=report.duplicate_topics,
        )
        return report

    async def _backfill_embeddings(self) -> int:
        missing = await self._topics.list_missing_embeddings()
        if not missing:
            return 0
        names = [t.canonical_name for t in missing]
        vectors = await asyncio.to_thread(self._embedder.embed_texts, names)
        for topic, vector in zip(missing, vectors, strict=True):
            if topic.id is not None:
                await self._topics.update_embedding(topic.id, vector)
        return len(missing)

    async def _build_clusters(self, topics: list[Topic]) -> list[ProposedCluster]:
        by_id = {t.id: t for t in topics if t.id is not None}
        uf = _UnionFind()
        for topic in topics:
            if topic.id is None or topic.embedding is None:
                continue
            uf.add(topic.id)
            neighbors = await self._topics.find_neighbors(
                embedding=topic.embedding,
                exclude_id=topic.id,
                max_distance=self._max_distance,
                limit=self._neighbor_limit,
            )
            for neighbor, _distance in neighbors:
                if neighbor.id is not None:
                    uf.union(topic.id, neighbor.id)

        mention_counts = await self._mentions.count_by_topic()

        clusters: list[ProposedCluster] = []
        for member_ids in uf.groups().values():
            members = [by_id[mid] for mid in member_ids if mid in by_id]
            if not members:
                continue
            canonical = self._choose_canonical(members, mention_counts)
            ordered = [canonical.canonical_name] + sorted(
                m.canonical_name for m in members if m.id != canonical.id
            )
            clusters.append(ProposedCluster(canonical=canonical.canonical_name, members=ordered))

        # Largest, most-duplicated clusters first.
        clusters.sort(key=lambda c: c.size, reverse=True)
        return clusters

    @staticmethod
    def _choose_canonical(members: list[Topic], mention_counts: dict[UUID, int]) -> Topic:
        """Most-mentioned topic wins; ties broken by shorter, then alphabetical name."""

        def key(topic: Topic) -> tuple[int, int, str]:
            count = mention_counts.get(topic.id, 0) if topic.id else 0
            return (-count, len(topic.canonical_name), topic.canonical_name.casefold())

        return min(members, key=key)
