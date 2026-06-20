"""SQLAlchemy ORM models.

Importing this package registers every model with ``Base.metadata`` so that
Alembic autogeneration and ``create_all`` see the full schema.
"""

from app.infrastructure.db.models.source import SourceModel
from app.infrastructure.db.models.topic import TopicModel
from app.infrastructure.db.models.topic_alias import TopicAliasModel
from app.infrastructure.db.models.topic_mention import TopicMentionModel
from app.infrastructure.db.models.trend_snapshot import TrendSnapshotModel

__all__ = [
    "SourceModel",
    "TopicAliasModel",
    "TopicMentionModel",
    "TopicModel",
    "TrendSnapshotModel",
]
