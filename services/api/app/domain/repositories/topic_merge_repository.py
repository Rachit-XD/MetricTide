"""Topic merge repository port.

Write operations that apply an approved merge: repoint mentions to the canonical
topic, record the merged-away name as an alias, and mark the merged topic
inactive. Kept separate from TopicRepository because these are consolidation
mutations, not ordinary topic persistence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RepointResult:
    repointed: int  # mentions moved to the canonical topic
    deduped: int  # mentions dropped because the source already mentioned canonical


class TopicMergeRepository(ABC):
    @abstractmethod
    async def repoint_mentions(self, from_topic_id: UUID, to_topic_id: UUID) -> RepointResult:
        """Move mentions from one topic to the canonical topic, dropping duplicates."""

    @abstractmethod
    async def add_alias(self, canonical_id: UUID, alias: str) -> None:
        """Record ``alias`` as resolving to the canonical topic (idempotent)."""

    @abstractmethod
    async def deactivate_topic(self, topic_id: UUID, merged_into_id: UUID) -> None:
        """Mark a topic inactive and record which canonical it merged into."""
