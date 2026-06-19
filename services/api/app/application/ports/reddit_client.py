"""Reddit client port.

Defines the contract the ingestion use case depends on, plus the lightweight
``RedditPost`` DTO it returns. Keeping this abstraction in the application layer
lets the HTTP/OAuth details stay in infrastructure and be swapped freely.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RedditPost:
    """A single post fetched from Reddit, normalized for ingestion."""

    external_id: str
    subreddit: str
    title: str
    content: str | None = None
    author: str | None = None
    score: int | None = None
    url: str | None = None
    # Original post time (Unix epoch seconds), from Reddit's `created_utc`.
    created_utc: float | None = None


class RedditClientPort(ABC):
    """Contract for fetching posts from Reddit."""

    @abstractmethod
    async def fetch_new(self, subreddit: str, limit: int = 100) -> list[RedditPost]:
        """Return the latest posts for ``subreddit`` (newest first).

        Raises an exception on transport/HTTP failure; callers decide whether to
        isolate per-subreddit failures.
        """
