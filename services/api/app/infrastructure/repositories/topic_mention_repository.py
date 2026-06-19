"""SQLAlchemy implementation of :class:`TopicMentionRepository`."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.topic_mention import TopicMention
from app.domain.exceptions import AlreadyExistsError
from app.domain.repositories.topic_mention_repository import TopicMentionRepository
from app.infrastructure.db.models.topic_mention import TopicMentionModel
from app.infrastructure.repositories.mappers import (
    topic_mention_to_entity,
    topic_mention_to_model,
)


class SqlAlchemyTopicMentionRepository(TopicMentionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, mention: TopicMention) -> TopicMention:
        model = topic_mention_to_model(mention)
        # SAVEPOINT isolates a unique-violation on (source_id, topic_id).
        try:
            async with self._session.begin_nested():
                self._session.add(model)
                await self._session.flush()
        except IntegrityError as exc:
            raise AlreadyExistsError(
                "topic mention already exists for this (source, topic)"
            ) from exc
        await self._session.refresh(model)
        return topic_mention_to_entity(model)

    async def list_for_topic(
        self, topic_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[TopicMention]:
        stmt = (
            select(TopicMentionModel)
            .where(TopicMentionModel.topic_id == topic_id)
            .order_by(TopicMentionModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [topic_mention_to_entity(m) for m in models]

    async def list_for_source(self, source_id: UUID) -> list[TopicMention]:
        stmt = select(TopicMentionModel).where(
            TopicMentionModel.source_id == source_id
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [topic_mention_to_entity(m) for m in models]
