"""TopicMention entity: links a Source to a Topic with a confidence score."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class TopicMention:
    """An association between a source and a topic produced by extraction.

    `confidence_score` is the extractor's confidence that the source discusses
    the topic, in the range [0.0, 1.0].
    """

    source_id: UUID
    topic_id: UUID
    confidence_score: float
    id: UUID | None = None
    created_at: datetime | None = None
