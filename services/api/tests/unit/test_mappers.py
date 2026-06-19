"""Tests that ORM <-> entity mappers copy fields faithfully (no database)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.domain.entities.source import Source
from app.domain.entities.platform import Platform
from app.infrastructure.db.models.source import SourceModel
from app.infrastructure.repositories.mappers import source_to_entity, source_to_model


def test_source_to_model_copies_fields() -> None:
    entity = Source(
        platform=Platform.REDDIT,
        external_id="abc123",
        title="Title",
        content="Body",
        author="alice",
        score=42,
        url="https://example.com",
    )

    model = source_to_model(entity)

    assert model.platform is Platform.REDDIT
    assert model.external_id == "abc123"
    assert model.score == 42


def test_source_to_entity_copies_fields() -> None:
    model = SourceModel(
        platform=Platform.HACKERNEWS,
        external_id="xyz",
        title="Title",
        content=None,
        author=None,
        score=None,
        url=None,
    )
    model.id = uuid.uuid4()
    model.created_at = datetime.now(UTC)

    entity = source_to_entity(model)

    assert entity.platform is Platform.HACKERNEWS
    assert entity.external_id == "xyz"
    assert entity.id == model.id
