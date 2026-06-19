"""FastAPI dependency providers (composition for the HTTP layer).

These assemble repositories, gateways, and use cases from a request-scoped DB
session. FastAPI caches each dependency per request, so the same ``AsyncSession``
is shared between the repository and the route handler that commits it.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.hackernews_client import HackerNewsClientPort
from app.application.ports.reddit_client import RedditClientPort
from app.application.use_cases.ingestion.hackernews import HackerNewsIngestionRunner
from app.application.use_cases.ingestion.reddit import RedditIngestionRunner
from app.application.use_cases.ingestion.source_ingestion_service import (
    SourceIngestionService,
)
from app.core.config import Settings, get_settings
from app.domain.repositories.source_repository import SourceRepository
from app.infrastructure.db.session import get_session
from app.infrastructure.hackernews.http_client import HttpHackerNewsClient
from app.infrastructure.reddit.http_client import HttpRedditClient
from app.infrastructure.repositories.source_repository import (
    SqlAlchemySourceRepository,
)

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_source_repository(session: SessionDep) -> SourceRepository:
    return SqlAlchemySourceRepository(session)


SourceRepositoryDep = Annotated[SourceRepository, Depends(get_source_repository)]


def get_source_ingestion_service(
    source_repository: SourceRepositoryDep,
) -> SourceIngestionService:
    return SourceIngestionService(source_repository=source_repository)


SourceIngestionServiceDep = Annotated[
    SourceIngestionService, Depends(get_source_ingestion_service)
]


# ---- Reddit ----
def get_reddit_client(settings: SettingsDep) -> RedditClientPort:
    return HttpRedditClient(
        base_url=settings.reddit_base_url,
        user_agent=settings.reddit_user_agent,
    )


RedditClientDep = Annotated[RedditClientPort, Depends(get_reddit_client)]


def get_reddit_ingestion_runner(
    reddit_client: RedditClientDep,
    ingestion_service: SourceIngestionServiceDep,
    settings: SettingsDep,
) -> RedditIngestionRunner:
    return RedditIngestionRunner(
        reddit_client=reddit_client,
        ingestion_service=ingestion_service,
        subreddits=settings.reddit_subreddit_list,
        fetch_limit=settings.reddit_fetch_limit,
    )


RedditIngestionRunnerDep = Annotated[
    RedditIngestionRunner, Depends(get_reddit_ingestion_runner)
]


# ---- Hacker News ----
def get_hackernews_client(settings: SettingsDep) -> HackerNewsClientPort:
    return HttpHackerNewsClient(
        base_url=settings.hackernews_base_url,
        user_agent=settings.hackernews_user_agent,
    )


HackerNewsClientDep = Annotated[HackerNewsClientPort, Depends(get_hackernews_client)]


def get_hackernews_ingestion_runner(
    hackernews_client: HackerNewsClientDep,
    ingestion_service: SourceIngestionServiceDep,
    settings: SettingsDep,
) -> HackerNewsIngestionRunner:
    return HackerNewsIngestionRunner(
        hackernews_client=hackernews_client,
        ingestion_service=ingestion_service,
        fetch_limit=settings.hackernews_fetch_limit,
    )


HackerNewsIngestionRunnerDep = Annotated[
    HackerNewsIngestionRunner, Depends(get_hackernews_ingestion_runner)
]
