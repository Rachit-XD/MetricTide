"""Canonical topic consolidation: apply semantic cluster recommendations.

Builds merge clusters from topic embeddings (pgvector cosine similarity), picks a
canonical per cluster by the rules below, and either previews (dry-run) or
applies the merge:

* repoint TopicMentions to the canonical topic (dropping duplicates),
* record each merged-away name as a TopicAlias,
* mark merged topics inactive (with merged_into_id for audit).

Canonical selection priority:
1. properly cased names (contain an uppercase letter),
2. highest mention count,
3. shortest meaningful name (ties favor the more-capitalized form).

Safety: apply is a separate, explicit step; merges are gated by a strict
similarity threshold and each member must be similar enough to the canonical.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from uuid import UUID

from app.application.use_cases.topics.topic_cluster_service import _UnionFind
from app.core.logging import get_logger
from app.domain.entities.topic import Topic
from app.domain.repositories.topic_mention_repository import TopicMentionRepository
from app.domain.repositories.topic_merge_repository import TopicMergeRepository
from app.domain.repositories.topic_repository import TopicRepository

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ClusterMember:
    topic: Topic
    similarity: float
    mention_count: int


@dataclass(slots=True)
class MergeCluster:
    canonical: Topic
    canonical_mentions: int
    members: list[ClusterMember] = field(default_factory=list)

    @property
    def size(self) -> int:
        return 1 + len(self.members)

    @property
    def min_similarity(self) -> float:
        return min((m.similarity for m in self.members), default=1.0)


@dataclass(slots=True)
class MergeReport:
    mode: str  # "preview" | "apply"
    clusters: list[MergeCluster]
    topics_merged: int
    mentions_repointed: int = 0
    mentions_deduped: int = 0


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


class CanonicalTopicService:
    def __init__(
        self,
        topic_repository: TopicRepository,
        mention_repository: TopicMentionRepository,
        merge_repository: TopicMergeRepository,
        similarity_threshold: float = 0.90,
        neighbor_limit: int = 10,
    ) -> None:
        self._topics = topic_repository
        self._mentions = mention_repository
        self._merge = merge_repository
        self._threshold = similarity_threshold
        self._neighbor_limit = neighbor_limit

    async def list_candidate_clusters(
        self, similarity_threshold: float
    ) -> list[MergeCluster]:
        """Broad clusters for review (read-only)."""
        return await self._build_clusters(similarity_threshold)

    async def preview(self) -> MergeReport:
        clusters = await self._build_clusters(self._threshold)
        return MergeReport(
            mode="preview",
            clusters=clusters,
            topics_merged=sum(len(c.members) for c in clusters),
        )

    async def apply(self) -> MergeReport:
        clusters = await self._build_clusters(self._threshold)
        repointed = 0
        deduped = 0
        merged = 0
        for cluster in clusters:
            for member in cluster.members:
                if member.topic.id is None or cluster.canonical.id is None:
                    continue
                result = await self._merge.repoint_mentions(
                    member.topic.id, cluster.canonical.id
                )
                repointed += result.repointed
                deduped += result.deduped
                await self._merge.add_alias(
                    cluster.canonical.id, member.topic.canonical_name
                )
                await self._merge.deactivate_topic(
                    member.topic.id, cluster.canonical.id
                )
                merged += 1

        logger.info(
            "topics.merge_applied",
            clusters=len(clusters),
            topics_merged=merged,
            mentions_repointed=repointed,
            mentions_deduped=deduped,
        )
        return MergeReport(
            mode="apply",
            clusters=clusters,
            topics_merged=merged,
            mentions_repointed=repointed,
            mentions_deduped=deduped,
        )

    async def _build_clusters(self, similarity_threshold: float) -> list[MergeCluster]:
        max_distance = 1.0 - similarity_threshold
        topics = await self._topics.list_with_embeddings()
        counts = await self._mentions.count_by_topic()
        by_id = {t.id: t for t in topics if t.id is not None}

        uf = _UnionFind()
        for topic in topics:
            if topic.id is None or topic.embedding is None:
                continue
            uf.add(topic.id)
            neighbors = await self._topics.find_neighbors(
                embedding=topic.embedding,
                exclude_id=topic.id,
                max_distance=max_distance,
                limit=self._neighbor_limit,
            )
            for neighbor, _distance in neighbors:
                if neighbor.id is not None:
                    uf.union(topic.id, neighbor.id)

        clusters: list[MergeCluster] = []
        for member_ids in uf.groups().values():
            members = [by_id[mid] for mid in member_ids if mid in by_id]
            if len(members) < 2:
                continue
            canonical = self._choose_canonical(members, counts)
            cluster_members: list[ClusterMember] = []
            for topic in members:
                if topic.id == canonical.id:
                    continue
                similarity = self._similarity(canonical, topic)
                # Each merged member must be close enough to the canonical
                # itself (guards against transitive chaining drift).
                if similarity < similarity_threshold:
                    continue
                cluster_members.append(
                    ClusterMember(
                        topic=topic,
                        similarity=round(similarity, 4),
                        mention_count=counts.get(topic.id, 0) if topic.id else 0,
                    )
                )
            if not cluster_members:
                continue
            cluster_members.sort(key=lambda m: m.similarity, reverse=True)
            clusters.append(
                MergeCluster(
                    canonical=canonical,
                    canonical_mentions=counts.get(canonical.id, 0)
                    if canonical.id
                    else 0,
                    members=cluster_members,
                )
            )

        clusters.sort(key=lambda c: c.size, reverse=True)
        return clusters

    @staticmethod
    def _similarity(a: Topic, b: Topic) -> float:
        if a.embedding is None or b.embedding is None:
            return 0.0
        return _cosine_similarity(a.embedding, b.embedding)

    @staticmethod
    def _choose_canonical(members: list[Topic], counts: dict[UUID, int]) -> Topic:
        def key(topic: Topic) -> tuple[int, int, int, str]:
            name = topic.canonical_name
            properly_cased = 0 if any(c.isupper() for c in name) else 1
            mention_count = counts.get(topic.id, 0) if topic.id else 0
            # Final str tiebreak favors the more-capitalized form (uppercase
            # sorts before lowercase), e.g. "ClickHouse" over "Clickhouse".
            return (properly_cased, -mention_count, len(name), name)

        return min(members, key=key)
