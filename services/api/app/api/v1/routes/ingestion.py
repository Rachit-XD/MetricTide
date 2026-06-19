"""Ingestion endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import (
    HackerNewsIngestionRunnerDep,
    RedditIngestionRunnerDep,
    SessionDep,
)
from app.api.v1.schemas.ingestion import IngestionRunResponse

router = APIRouter()


@router.post(
    "/reddit/run",
    response_model=IngestionRunResponse,
    summary="Run Reddit ingestion",
)
async def run_reddit_ingestion(
    runner: RedditIngestionRunnerDep,
    session: SessionDep,
) -> IngestionRunResponse:
    """Fetch the latest posts from the configured subreddits and persist new ones."""
    result = await runner.run()
    await session.commit()
    return IngestionRunResponse(
        fetched=result.fetched,
        inserted=result.inserted,
        skipped=result.skipped,
    )


@router.post(
    "/hackernews/run",
    response_model=IngestionRunResponse,
    summary="Run Hacker News ingestion",
)
async def run_hackernews_ingestion(
    runner: HackerNewsIngestionRunnerDep,
    session: SessionDep,
) -> IngestionRunResponse:
    """Fetch current top Hacker News stories and persist new ones.

    The route is the unit-of-work boundary: it commits on success; the session
    dependency rolls back on error.
    """
    result = await runner.run()
    await session.commit()
    return IngestionRunResponse(
        fetched=result.fetched,
        inserted=result.inserted,
        skipped=result.skipped,
    )
