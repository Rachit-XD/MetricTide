"""HTTP implementation of :class:`HackerNewsClientPort`.

Uses the public Hacker News Firebase API (no auth):

* ``/topstories.json``  -> ordered list of story ids
* ``/item/{id}.json``   -> a single item

Item fetches run concurrently (bounded by a semaphore); individual failures are
logged and skipped so the batch still returns the stories that succeeded.
"""

from __future__ import annotations

import asyncio
from typing import Any, cast

import httpx

from app.application.ports.hackernews_client import (
    HackerNewsClientPort,
    HackerNewsStory,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class HttpHackerNewsClient(HackerNewsClientPort):
    def __init__(
        self,
        base_url: str,
        user_agent: str,
        timeout: float = 10.0,
        concurrency: int = 10,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._user_agent = user_agent
        self._timeout = timeout
        self._concurrency = concurrency

    async def fetch_top_stories(self, limit: int = 50) -> list[HackerNewsStory]:
        headers = {"User-Agent": self._user_agent}
        async with httpx.AsyncClient(timeout=self._timeout, headers=headers) as client:
            response = await client.get(f"{self._base_url}/topstories.json")
            response.raise_for_status()
            story_ids: list[int] = response.json()[:limit]

            semaphore = asyncio.Semaphore(self._concurrency)

            async def fetch_item(item_id: int) -> dict[str, Any]:
                async with semaphore:
                    item_response = await client.get(f"{self._base_url}/item/{item_id}.json")
                    item_response.raise_for_status()
                    # httpx's .json() is typed as Any; HN items are JSON objects.
                    return cast(dict[str, Any], item_response.json())

            results = await asyncio.gather(
                *(fetch_item(i) for i in story_ids), return_exceptions=True
            )

        stories: list[HackerNewsStory] = []
        for result in results:
            if isinstance(result, BaseException):
                logger.warning("hackernews.item_failed", error=str(result))
                continue
            story = self._to_story(result)
            if story is not None:
                stories.append(story)

        logger.info("hackernews.fetched", requested=len(story_ids), stories=len(stories))
        return stories

    @staticmethod
    def _to_story(data: dict[str, Any] | None) -> HackerNewsStory | None:
        if not data or data.get("type") != "story":
            return None
        if data.get("dead") or data.get("deleted"):
            return None
        title = data.get("title")
        if not title:
            return None
        return HackerNewsStory(
            id=int(data["id"]),
            title=title,
            url=data.get("url"),
            score=data.get("score"),
            by=data.get("by"),
            time=data.get("time"),
        )
