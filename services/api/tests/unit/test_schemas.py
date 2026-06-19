"""Validation tests for the v1 Pydantic schemas (no database required)."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.api.v1.schemas.source import SourceCreate
from app.api.v1.schemas.topic_mention import TopicMentionCreate
from app.domain.entities.platform import Platform


def test_source_create_accepts_minimal_payload() -> None:
    payload = SourceCreate(platform=Platform.REDDIT, external_id="abc123", title="Hello")
    assert payload.platform is Platform.REDDIT
    assert payload.content is None


def test_topic_mention_confidence_must_be_within_unit_interval() -> None:
    with pytest.raises(ValidationError):
        TopicMentionCreate(
            source_id=uuid.uuid4(),
            topic_id=uuid.uuid4(),
            confidence_score=1.5,
        )
