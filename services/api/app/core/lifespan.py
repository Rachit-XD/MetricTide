"""Application lifespan management.

Startup/shutdown hooks live here. Resource initialization (DB engine, Redis
pool, etc.) will be wired in as features land — for now this only logs the
boundaries so container orchestration and health checks have clear signals.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup and shutdown of application-wide resources."""
    settings = get_settings()
    logger.info("api.startup", environment=settings.environment.value)

    # TODO: initialize DB engine, Redis pool, and other resources here.

    yield

    logger.info("api.shutdown")
    # TODO: dispose DB engine, close Redis pool, etc.
