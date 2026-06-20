"""TopicAlias entity: an alternate surface form mapped to a canonical topic.

Created when topics are merged, so the original (merged-away) names are
preserved and can later resolve to the canonical topic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class TopicAlias:
    topic_id: UUID  # the canonical topic this alias resolves to
    alias: str
    id: UUID | None = None
    created_at: datetime | None = None
