"""Repository interfaces (ports).

Abstract contracts that the application layer depends on. Concrete
implementations live in ``app/infrastructure/repositories``.
"""

from app.domain.repositories.source_repository import SourceRepository
from app.domain.repositories.topic_mention_repository import TopicMentionRepository
from app.domain.repositories.topic_repository import TopicRepository
from app.domain.repositories.trend_snapshot_repository import TrendSnapshotRepository

__all__ = [
    "SourceRepository",
    "TopicMentionRepository",
    "TopicRepository",
    "TrendSnapshotRepository",
]
