"""Source repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.platform import Platform
from app.domain.entities.source import Source


class SourceRepository(ABC):
    """Persistence contract for :class:`Source` aggregates."""

    @abstractmethod
    async def add(self, source: Source) -> Source:
        """Persist a new source and return it with its assigned id."""

    @abstractmethod
    async def get_by_id(self, source_id: UUID) -> Source | None:
        """Return the source with the given id, or ``None``."""

    @abstractmethod
    async def get_by_external_id(
        self, platform: Platform, external_id: str
    ) -> Source | None:
        """Return the source uniquely identified by ``(platform, external_id)``."""

    @abstractmethod
    async def list_recent(self, limit: int = 100, offset: int = 0) -> list[Source]:
        """Return sources ordered by most recently created."""
