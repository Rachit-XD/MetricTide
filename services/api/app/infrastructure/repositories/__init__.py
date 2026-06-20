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
from app.infrastructure.repositories.topic_merge_repository import (
    SqlAlchemyTopicMergeRepository,
)
from app.infrastructure.repositories.topic_repository import SqlAlchemyTopicRepository
from app.infrastructure.repositories.trend_metrics_repository import (
    SqlAlchemyTrendMetricsRepository,
)
from app.infrastructure.repositories.trend_snapshot_repository import (
    SqlAlchemyTrendSnapshotRepository,
)

__all__ = [
    "SqlAlchemySourceRepository",
    "SqlAlchemyTopicMentionRepository",
    "SqlAlchemyTopicMergeRepository",
    "SqlAlchemyTopicRepository",
    "SqlAlchemyTrendMetricsRepository",
    "SqlAlchemyTrendSnapshotRepository",
]
