"""Hacker News client port.

Defines the contract the HN ingestion runner depends on, plus the lightweight
``HackerNewsStory`` DTO it returns. Implementations live in infrastructure.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HackerNewsStory:
    """A single Hacker News story, normalized for ingestion.

    ``time`` is the story's original creation time (Unix epoch seconds), as
    reported by the HN API.
    """

    id: int
    title: str
    url: str | None = None
    score: int | None = None
    by: str | None = None
    time: int | None = None


class HackerNewsClientPort(ABC):
    """Contract for fetching stories from Hacker News."""

    @abstractmethod
    async def fetch_top_stories(self, limit: int = 50) -> list[HackerNewsStory]:
        """Return up to ``limit`` current top stories.

        Raises on failure to fetch the story-id listing; individual item
        failures are skipped so a single bad item never aborts the batch.
        """
