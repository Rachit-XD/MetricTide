"""Domain entities.

Plain, framework-agnostic models representing core concepts: Source, Topic,
TopicMention, and TrendSnapshot.
"""

from app.domain.entities.platform import Platform
from app.domain.entities.source import Source
from app.domain.entities.topic import Topic
from app.domain.entities.topic_alias import TopicAlias
from app.domain.entities.topic_mention import TopicMention
from app.domain.entities.trend_snapshot import TrendSnapshot

__all__ = [
    "Platform",
    "Source",
    "Topic",
    "TopicAlias",
    "TopicMention",
    "TrendSnapshot",
]
