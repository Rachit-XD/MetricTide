"""Async Redis client factory.

Created lazily and cached for the process. No connection is opened at import
time; the first command lazily establishes the pool.
"""

from __future__ import annotations

from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import get_settings


@lru_cache
def get_redis() -> Redis:
    """Return the process-wide async Redis client."""
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)
