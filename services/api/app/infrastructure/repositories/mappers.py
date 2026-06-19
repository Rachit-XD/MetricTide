"""Translation between ORM models and pure domain entities.

Keeping mapping in one place lets repositories return framework-free entities
while the persistence details stay in the infrastructure layer.
"""

from __future__ import annotations

from app.domain.entities.source import Source
from app.domain.entities.topic import Topic
from app.domain.entities.topic_mention import TopicMention
from app.domain.entities.trend_snapshot import TrendSnapshot
from app.infrastructure.db.models.source import SourceModel
from app.infrastructure.db.models.topic import TopicModel
from app.infrastructure.db.models.topic_mention import TopicMentionModel
from app.infrastructure.db.models.trend_snapshot import TrendSnapshotModel


def source_to_entity(model: SourceModel) -> Source:
    return Source(
        id=model.id,
        platform=model.platform,
        external_id=model.external_id,
        title=model.title,
        content=model.content,
        author=model.author,
        score=model.score,
        url=model.url,
        source_created_at=model.source_created_at,
        created_at=model.created_at,
    )


def source_to_model(entity: Source) -> SourceModel:
    return SourceModel(
        platform=entity.platform,
        external_id=entity.external_id,
        title=entity.title,
        content=entity.content,
        author=entity.author,
        score=entity.score,
        url=entity.url,
        source_created_at=entity.source_created_at,
    )


def topic_to_entity(model: TopicModel) -> Topic:
    return Topic(
        id=model.id,
        canonical_name=model.canonical_name,
        description=model.description,
        embedding=list(model.embedding) if model.embedding is not None else None,
        created_at=model.created_at,
    )


def topic_to_model(entity: Topic) -> TopicModel:
    return TopicModel(
        canonical_name=entity.canonical_name,
        description=entity.description,
        embedding=entity.embedding,
    )


def topic_mention_to_entity(model: TopicMentionModel) -> TopicMention:
    return TopicMention(
        id=model.id,
        source_id=model.source_id,
        topic_id=model.topic_id,
        confidence_score=model.confidence_score,
        created_at=model.created_at,
    )


def topic_mention_to_model(entity: TopicMention) -> TopicMentionModel:
    return TopicMentionModel(
        source_id=entity.source_id,
        topic_id=entity.topic_id,
        confidence_score=entity.confidence_score,
    )


def trend_snapshot_to_entity(model: TrendSnapshotModel) -> TrendSnapshot:
    return TrendSnapshot(
        id=model.id,
        topic_id=model.topic_id,
        snapshot_date=model.snapshot_date,
        mention_count=model.mention_count,
        engagement_score=model.engagement_score,
        growth_rate=model.growth_rate,
        trend_score=model.trend_score,
        created_at=model.created_at,
    )


def trend_snapshot_to_model(entity: TrendSnapshot) -> TrendSnapshotModel:
    return TrendSnapshotModel(
        topic_id=entity.topic_id,
        snapshot_date=entity.snapshot_date,
        mention_count=entity.mention_count,
        engagement_score=entity.engagement_score,
        growth_rate=entity.growth_rate,
        trend_score=entity.trend_score,
    )
