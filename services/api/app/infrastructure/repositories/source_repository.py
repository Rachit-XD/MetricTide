"""SQLAlchemy implementation of :class:`SourceRepository`."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.platform import Platform
from app.domain.entities.source import Source
from app.domain.repositories.source_repository import SourceRepository
from app.infrastructure.db.models.source import SourceModel
from app.infrastructure.repositories.mappers import source_to_entity, source_to_model


class SqlAlchemySourceRepository(SourceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, source: Source) -> Source:
        model = source_to_model(source)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return source_to_entity(model)

    async def get_by_id(self, source_id: UUID) -> Source | None:
        model = await self._session.get(SourceModel, source_id)
        return source_to_entity(model) if model is not None else None

    async def get_by_external_id(
        self, platform: Platform, external_id: str
    ) -> Source | None:
        stmt = select(SourceModel).where(
            SourceModel.platform == platform,
            SourceModel.external_id == external_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return source_to_entity(model) if model is not None else None

    async def list_recent(self, limit: int = 100, offset: int = 0) -> list[Source]:
        stmt = (
            select(SourceModel)
            .order_by(SourceModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [source_to_entity(m) for m in models]
