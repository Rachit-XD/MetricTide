"""SQLAlchemy implementation of :class:`TopicMergeRepository`."""

from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from sqlalchemy import CursorResult, delete, exists, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.topic_merge_repository import (
    RepointResult,
    TopicMergeRepository,
)
from app.infrastructure.db.models.topic import TopicModel
from app.infrastructure.db.models.topic_alias import TopicAliasModel
from app.infrastructure.db.models.topic_mention import TopicMentionModel


class SqlAlchemyTopicMergeRepository(TopicMergeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def repoint_mentions(
        self, from_topic_id: UUID, to_topic_id: UUID
    ) -> RepointResult:
        # 1. Drop mentions of the merged topic whose source already mentions the
        #    canonical topic (they would violate uq_topic_mentions_source_topic).
        canonical = TopicMentionModel.__table__.alias("canonical")
        dup_stmt = delete(TopicMentionModel).where(
            TopicMentionModel.topic_id == from_topic_id,
            exists().where(
                canonical.c.topic_id == to_topic_id,
                canonical.c.source_id == TopicMentionModel.source_id,
            ),
        )
        deduped = cast("CursorResult[Any]", await self._session.execute(dup_stmt)).rowcount

        # 2. Repoint the remaining mentions to the canonical topic.
        repoint_stmt = (
            update(TopicMentionModel)
            .where(TopicMentionModel.topic_id == from_topic_id)
            .values(topic_id=to_topic_id)
        )
        repointed = cast(
            "CursorResult[Any]", await self._session.execute(repoint_stmt)
        ).rowcount

        return RepointResult(repointed=repointed, deduped=deduped)

    async def add_alias(self, canonical_id: UUID, alias: str) -> None:
        stmt = (
            pg_insert(TopicAliasModel)
            .values(topic_id=canonical_id, alias=alias)
            .on_conflict_do_nothing(constraint="uq_topic_aliases_alias")
        )
        await self._session.execute(stmt)

    async def deactivate_topic(self, topic_id: UUID, merged_into_id: UUID) -> None:
        await self._session.execute(
            update(TopicModel)
            .where(TopicModel.id == topic_id)
            .values(is_active=False, merged_into_id=merged_into_id)
        )
