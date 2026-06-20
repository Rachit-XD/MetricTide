"""Topic repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.topic import Topic


class TopicRepository(ABC):
    """Persistence contract for :class:`Topic` aggregates."""

    @abstractmethod
    async def add(self, topic: Topic) -> Topic:
        """Persist a new topic and return it with its assigned id."""

    @abstractmethod
    async def get_by_id(self, topic_id: UUID) -> Topic | None:
        """Return the topic with the given id, or ``None``."""

    @abstractmethod
    async def get_by_canonical_name(self, canonical_name: str) -> Topic | None:
        """Return the topic with the given canonical name, or ``None``."""

    @abstractmethod
    async def search_similar(
        self, embedding: list[float], limit: int = 10
    ) -> list[Topic]:
        """Return topics nearest to ``embedding`` by cosine distance (pgvector)."""

    @abstractmethod
    async def list_all(self, limit: int = 1000, offset: int = 0) -> list[Topic]:
        """Return topics ordered by canonical name."""

    @abstractmethod
    async def list_missing_embeddings(self, limit: int = 1000) -> list[Topic]:
        """Return topics that have no embedding yet."""

    @abstractmethod
    async def list_with_embeddings(self, limit: int = 5000) -> list[Topic]:
        """Return topics that have an embedding."""

    @abstractmethod
    async def update_embedding(self, topic_id: UUID, embedding: list[float]) -> None:
        """Persist the embedding for a topic."""

    @abstractmethod
    async def find_neighbors(
        self,
        embedding: list[float],
        exclude_id: UUID,
        max_distance: float,
        limit: int = 10,
    ) -> list[tuple[Topic, float]]:
        """Return (topic, cosine_distance) within ``max_distance``, excluding ``exclude_id``."""
