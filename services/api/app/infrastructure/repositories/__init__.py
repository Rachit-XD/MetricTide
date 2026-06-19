"""Concrete repository implementations.

SQLAlchemy-backed implementations of the ports defined in
``app/domain/repositories``.
"""

from app.infrastructure.repositories.source_repository import (
    SqlAlchemySourceRepository,
)
from app.infrastructure.repositories.topic_mention_repository import (
    SqlAlchemyTopicMentionRepository,
)
from app.infrastructure.repositories.topic_repository import SqlAlchemyTopicRepository
from app.infrastructure.repositories.trend_snapshot_repository import (
    SqlAlchemyTrendSnapshotRepository,
)

__all__ = [
    "SqlAlchemySourceRepository",
    "SqlAlchemyTopicRepository",
    "SqlAlchemyTopicMentionRepository",
    "SqlAlchemyTrendSnapshotRepository",
]
