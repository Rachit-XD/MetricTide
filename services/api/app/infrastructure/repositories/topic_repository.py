"""SQLAlchemy implementation of :class:`TopicRepository`."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.topic import Topic
from app.domain.exceptions import AlreadyExistsError
from app.domain.repositories.topic_repository import TopicRepository
from app.infrastructure.db.models.topic import TopicModel
from app.infrastructure.repositories.mappers import topic_to_entity, topic_to_model


class SqlAlchemyTopicRepository(TopicRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, topic: Topic) -> Topic:
        model = topic_to_model(topic)
        # SAVEPOINT isolates a unique-violation (duplicate canonical_name) so it
        # rolls back only this insert, not the surrounding transaction.
        try:
            async with self._session.begin_nested():
                self._session.add(model)
                await self._session.flush()
        except IntegrityError as exc:
            raise AlreadyExistsError(
                f"topic '{topic.canonical_name}' already exists"
            ) from exc
        await self._session.refresh(model)
        return topic_to_entity(model)

    async def get_by_id(self, topic_id: UUID) -> Topic | None:
        model = await self._session.get(TopicModel, topic_id)
        return topic_to_entity(model) if model is not None else None

    async def get_by_canonical_name(self, canonical_name: str) -> Topic | None:
        stmt = select(TopicModel).where(TopicModel.canonical_name == canonical_name)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return topic_to_entity(model) if model is not None else None

    async def search_similar(
        self, embedding: list[float], limit: int = 10
    ) -> list[Topic]:
        # pgvector cosine distance operator, exposed via the ORM column.
        stmt = (
            select(TopicModel)
            .where(TopicModel.embedding.is_not(None))
            .order_by(TopicModel.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [topic_to_entity(m) for m in models]
