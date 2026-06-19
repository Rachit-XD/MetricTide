"""HTTP implementation of :class:`RedditClientPort`.

Uses Reddit's public listing endpoint (``/r/{subreddit}/new.json``), which
requires no OAuth — only a descriptive ``User-Agent``. The response is mapped
into ``RedditPost`` DTOs. To move to the authenticated API later, add an
OAuth-based client implementing the same port; nothing else needs to change.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.application.ports.reddit_client import RedditClientPort, RedditPost
from app.core.logging import get_logger

logger = get_logger(__name__)


class HttpRedditClient(RedditClientPort):
    def __init__(
        self,
        base_url: str,
        user_agent: str,
        timeout: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._user_agent = user_agent
        self._timeout = timeout

    async def fetch_new(self, subreddit: str, limit: int = 100) -> list[RedditPost]:
        url = f"{self._base_url}/r/{subreddit}/new.json"
        headers = {"User-Agent": self._user_agent}

        async with httpx.AsyncClient(timeout=self._timeout, headers=headers) as client:
            response = await client.get(url, params={"limit": limit})
            response.raise_for_status()
            payload = response.json()

        children = payload.get("data", {}).get("children", [])
        posts = [self._to_post(child.get("data", {}), subreddit) for child in children]
        logger.info("reddit.fetched", subreddit=subreddit, count=len(posts))
        return posts

    def _to_post(self, data: dict[str, Any], subreddit: str) -> RedditPost:
        permalink = data.get("permalink")
        url = f"{self._base_url}{permalink}" if permalink else data.get("url")
        selftext = data.get("selftext") or None
        return RedditPost(
            external_id=str(data["id"]),
            subreddit=subreddit,
            title=data.get("title", ""),
            content=selftext,
            author=data.get("author"),
            score=data.get("score"),
            url=url,
            created_utc=data.get("created_utc"),
        )
