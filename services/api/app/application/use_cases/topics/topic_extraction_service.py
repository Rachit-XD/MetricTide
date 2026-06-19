"""Topic extraction use case: Source -> Topic -> TopicMention.

For each source: extract candidate topics, normalize them, create topics that
don't exist (reuse those that do), and create a TopicMention per (source, topic)
with a confidence score. Deduplicates mentions on (source_id, topic_id).

No clustering, embeddings, or trend scoring here.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from uuid import UUID

from app.application.ports.topic_extraction import TopicExtractionPort
from app.application.use_cases.topics.normalizer import TopicNormalizer
from app.core.logging import get_logger
from app.domain.entities.topic import Topic
from app.domain.entities.topic_mention import TopicMention
from app.domain.exceptions import AlreadyExistsError
from app.domain.repositories.source_repository import SourceRepository
from app.domain.repositories.topic_mention_repository import TopicMentionRepository
from app.domain.repositories.topic_repository import TopicRepository

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class TopicExtractionResult:
    sources_processed: int
    topics_created: int
    mentions_created: int


class TopicExtractionService:
    def __init__(
        self,
        extractor: TopicExtractionPort,
        normalizer: TopicNormalizer,
        source_repository: SourceRepository,
        topic_repository: TopicRepository,
        mention_repository: TopicMentionRepository,
        min_confidence: float = 0.3,
        source_limit: int = 500,
    ) -> None:
        self._extractor = extractor
        self._normalizer = normalizer
        self._sources = source_repository
        self._topics = topic_repository
        self._mentions = mention_repository
        self._min_confidence = min_confidence
        self._source_limit = source_limit

    async def run(self) -> TopicExtractionResult:
        sources_processed = 0
        topics_created = 0
        mentions_created = 0
        # Cache canonical_name -> topic_id for the duration of the run.
        topic_ids: dict[str, UUID] = {}

        sources = await self._sources.list_recent(limit=self._source_limit)
        for source in sources:
            sources_processed += 1
            if source.id is None:
                continue

            candidates = self._normalized_candidates(
                await asyncio.to_thread(self._extractor.extract, self._text_for(source))
            )
            if not candidates:
                continue

            existing_mentions = {
                m.topic_id for m in await self._mentions.list_for_source(source.id)
            }

            for canonical, confidence in candidates.items():
                topic_id, created = await self._get_or_create_topic(canonical, topic_ids)
                if created:
                    topics_created += 1
                if topic_id in existing_mentions:
                    continue
                if await self._create_mention(source.id, topic_id, confidence):
                    mentions_created += 1
                    existing_mentions.add(topic_id)

        logger.info(
            "topics.extraction_completed",
            sources_processed=sources_processed,
            topics_created=topics_created,
            mentions_created=mentions_created,
        )
        return TopicExtractionResult(
            sources_processed=sources_processed,
            topics_created=topics_created,
            mentions_created=mentions_created,
        )

    @staticmethod
    def _text_for(source) -> str:  # type: ignore[no-untyped-def]
        if source.content:
            return f"{source.title}. {source.content}"
        return source.title

    def _normalized_candidates(self, extracted) -> dict[str, float]:  # type: ignore[no-untyped-def]
        """Normalize and merge candidates by canonical name, keeping the max confidence."""
        best: dict[str, float] = {}
        for candidate in extracted:
            if candidate.confidence < self._min_confidence:
                continue
            canonical = self._normalizer.normalize(candidate.name)
            if canonical is None:
                continue
            best[canonical] = max(best.get(canonical, 0.0), candidate.confidence)
        return best

    async def _get_or_create_topic(
        self, canonical: str, cache: dict[str, UUID]
    ) -> tuple[UUID, bool]:
        cached = cache.get(canonical)
        if cached is not None:
            return cached, False

        existing = await self._topics.get_by_canonical_name(canonical)
        if existing is not None and existing.id is not None:
            cache[canonical] = existing.id
            return existing.id, False

        try:
            created = await self._topics.add(Topic(canonical_name=canonical))
        except AlreadyExistsError:
            # Race: created elsewhere; re-fetch.
            existing = await self._topics.get_by_canonical_name(canonical)
            assert existing is not None and existing.id is not None
            cache[canonical] = existing.id
            return existing.id, False

        assert created.id is not None
        cache[canonical] = created.id
        return created.id, True

    async def _create_mention(
        self, source_id: UUID, topic_id: UUID, confidence: float
    ) -> bool:
        try:
            await self._mentions.add(
                TopicMention(
                    source_id=source_id,
                    topic_id=topic_id,
                    confidence_score=confidence,
                )
            )
        except AlreadyExistsError:
            return False
        return True
