"""FastAPI dependency providers (composition for the HTTP layer).

These assemble repositories, gateways, and use cases from a request-scoped DB
session. FastAPI caches each dependency per request, so the same ``AsyncSession``
is shared between the repository and the route handler that commits it.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.embedding import EmbeddingPort
from app.application.ports.hackernews_client import HackerNewsClientPort
from app.application.ports.reddit_client import RedditClientPort
from app.application.ports.topic_extraction import TopicExtractionPort
from app.application.use_cases.ingestion.hackernews import HackerNewsIngestionRunner
from app.application.use_cases.ingestion.reddit import RedditIngestionRunner
from app.application.use_cases.ingestion.source_ingestion_service import (
    SourceIngestionService,
)
from app.application.use_cases.topics.normalizer import TopicNormalizer
from app.application.use_cases.topics.topic_cluster_service import TopicClusterService
from app.application.use_cases.topics.topic_extraction_service import (
    TopicExtractionService,
)
from app.application.use_cases.trends.trend_score_calculator import (
    ScoreWeights,
    TrendScoreCalculator,
)
from app.application.use_cases.trends.trend_scoring_service import TrendScoringService
from app.core.config import Settings, get_settings
from app.domain.repositories.source_repository import SourceRepository
from app.domain.repositories.topic_mention_repository import TopicMentionRepository
from app.domain.repositories.topic_repository import TopicRepository
from app.domain.repositories.trend_metrics_repository import TrendMetricsRepository
from app.domain.repositories.trend_snapshot_repository import TrendSnapshotRepository
from app.infrastructure.db.session import get_session
from app.infrastructure.hackernews.http_client import HttpHackerNewsClient
from app.infrastructure.reddit.http_client import HttpRedditClient
from app.infrastructure.repositories.source_repository import (
    SqlAlchemySourceRepository,
)
from app.infrastructure.repositories.topic_mention_repository import (
    SqlAlchemyTopicMentionRepository,
)
from app.infrastructure.repositories.topic_repository import SqlAlchemyTopicRepository
from app.infrastructure.repositories.trend_metrics_repository import (
    SqlAlchemyTrendMetricsRepository,
)
from app.infrastructure.repositories.trend_snapshot_repository import (
    SqlAlchemyTrendSnapshotRepository,
)

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_source_repository(session: SessionDep) -> SourceRepository:
    return SqlAlchemySourceRepository(session)


SourceRepositoryDep = Annotated[SourceRepository, Depends(get_source_repository)]


def get_topic_repository(session: SessionDep) -> TopicRepository:
    return SqlAlchemyTopicRepository(session)


TopicRepositoryDep = Annotated[TopicRepository, Depends(get_topic_repository)]


def get_topic_mention_repository(session: SessionDep) -> TopicMentionRepository:
    return SqlAlchemyTopicMentionRepository(session)


TopicMentionRepositoryDep = Annotated[
    TopicMentionRepository, Depends(get_topic_mention_repository)
]


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


# ---- Topic extraction ----
@lru_cache(maxsize=1)
def get_topic_extractor() -> TopicExtractionPort:
    """Process-wide singleton: heavy NLP models load once on first use."""
    # Imported lazily so the (heavy) ML stack is only required where it is used.
    from app.infrastructure.nlp.spacy_keybert_extractor import (
        SpacyKeyBertTopicExtractor,
    )

    settings = get_settings()
    return SpacyKeyBertTopicExtractor(
        spacy_model=settings.spacy_model,
        embedding_model=settings.embedding_model,
        top_n=settings.keybert_top_n,
        ner_confidence=settings.ner_confidence,
    )


def get_topic_extraction_service(
    source_repository: SourceRepositoryDep,
    topic_repository: TopicRepositoryDep,
    mention_repository: TopicMentionRepositoryDep,
    settings: SettingsDep,
) -> TopicExtractionService:
    return TopicExtractionService(
        extractor=get_topic_extractor(),
        normalizer=TopicNormalizer(),
        source_repository=source_repository,
        topic_repository=topic_repository,
        mention_repository=mention_repository,
        min_confidence=settings.topic_min_confidence,
        source_limit=settings.extract_source_limit,
    )


TopicExtractionServiceDep = Annotated[
    TopicExtractionService, Depends(get_topic_extraction_service)
]


# ---- Topic clustering ----
@lru_cache(maxsize=1)
def get_embedder() -> EmbeddingPort:
    """Process-wide singleton: the embedding model loads once on first use."""
    from app.infrastructure.nlp.sentence_transformer_embedder import (
        SentenceTransformerEmbedder,
    )

    return SentenceTransformerEmbedder(model_name=get_settings().embedding_model)


def get_topic_cluster_service(
    topic_repository: TopicRepositoryDep,
    mention_repository: TopicMentionRepositoryDep,
    settings: SettingsDep,
) -> TopicClusterService:
    return TopicClusterService(
        embedder=get_embedder(),
        topic_repository=topic_repository,
        mention_repository=mention_repository,
        similarity_threshold=settings.cluster_similarity_threshold,
        neighbor_limit=settings.cluster_neighbor_limit,
    )


TopicClusterServiceDep = Annotated[
    TopicClusterService, Depends(get_topic_cluster_service)
]


# ---- Trend scoring ----
def get_trend_metrics_repository(session: SessionDep) -> TrendMetricsRepository:
    return SqlAlchemyTrendMetricsRepository(session)


TrendMetricsRepositoryDep = Annotated[
    TrendMetricsRepository, Depends(get_trend_metrics_repository)
]


def get_trend_snapshot_repository(session: SessionDep) -> TrendSnapshotRepository:
    return SqlAlchemyTrendSnapshotRepository(session)


TrendSnapshotRepositoryDep = Annotated[
    TrendSnapshotRepository, Depends(get_trend_snapshot_repository)
]


def get_trend_scoring_service(
    metrics_repository: TrendMetricsRepositoryDep,
    snapshot_repository: TrendSnapshotRepositoryDep,
    settings: SettingsDep,
) -> TrendScoringService:
    calculator = TrendScoreCalculator(
        ScoreWeights(
            mentions=settings.trend_weight_mentions,
            engagement=settings.trend_weight_engagement,
            diversity=settings.trend_weight_diversity,
            recency=settings.trend_weight_recency,
        )
    )
    return TrendScoringService(
        metrics_repository=metrics_repository,
        snapshot_repository=snapshot_repository,
        calculator=calculator,
        recency_half_life_hours=settings.trend_recency_half_life_hours,
    )


TrendScoringServiceDep = Annotated[
    TrendScoringService, Depends(get_trend_scoring_service)
]
