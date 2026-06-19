"""Source platforms.

A domain-level enum shared by entities and (downstream) the ORM. Extend this as
new ingestion sources are added; the database enum type is migrated in lockstep.
"""

from __future__ import annotations

from enum import Enum


class Platform(str, Enum):
    REDDIT = "reddit"
    HACKERNEWS = "hackernews"
