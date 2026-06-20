"""TopicMention repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.topic_mention import TopicMention


class TopicMentionRepository(ABC):
    """Persistence contract for :class:`TopicMention` aggregates."""

    @abstractmethod
    async def add(self, mention: TopicMention) -> TopicMention:
        """Persist a new mention and return it with its assigned id."""

    @abstractmethod
    async def list_for_topic(
        self, topic_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[TopicMention]:
        """Return mentions for a given topic."""

    @abstractmethod
    async def list_for_source(self, source_id: UUID) -> list[TopicMention]:
        """Return mentions for a given source."""

    @abstractmethod
    async def count_by_topic(self) -> dict[UUID, int]:
        """Return a mapping of topic_id -> number of mentions."""
