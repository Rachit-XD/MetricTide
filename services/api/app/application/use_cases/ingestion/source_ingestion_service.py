"""Source ingestion: deduplicate and persist candidate sources.

This service is platform-agnostic. Platform-specific fetching and mapping live
in per-source runners (see ``reddit.py`` and ``hackernews.py``), which hand a
list of already-mapped :class:`Source` candidates to :meth:`ingest`.

Deduplication on ``(platform, external_id)`` happens in three layers: an in-run
``seen`` set, a pre-insert repository lookup, and a DB-constraint backstop
surfaced as :class:`AlreadyExistsError`.

No embeddings, clustering, topic extraction, or scoring happen here — only
reliable deduplication and persistence.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.core.logging import get_logger
from app.domain.entities.source import Source
from app.domain.exceptions import AlreadyExistsError
from app.domain.repositories.source_repository import SourceRepository

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Outcome of an ingestion run."""

    fetched: int
    inserted: int
    skipped: int


class SourceIngestionService:
    def __init__(self, source_repository: SourceRepository) -> None:
        self._sources = source_repository

    async def ingest(self, candidates: Sequence[Source]) -> IngestionResult:
        """Persist new sources from ``candidates``; skip duplicates.

        ``fetched`` is the number of candidates supplied (including in-batch
        duplicates); ``skipped`` counts duplicates (in-batch + already stored).
        """
        fetched = len(candidates)
        inserted = 0
        skipped = 0
        seen: set[tuple[str, str]] = set()

        for source in candidates:
            if await self._persist(source, seen):
                inserted += 1
            else:
                skipped += 1

        logger.info(
            "ingestion.completed", fetched=fetched, inserted=inserted, skipped=skipped
        )
        return IngestionResult(fetched=fetched, inserted=inserted, skipped=skipped)

    async def _persist(self, source: Source, seen: set[tuple[str, str]]) -> bool:
        """Persist a single source. Returns ``True`` if inserted, ``False`` if skipped."""
        key = (source.platform.value, source.external_id)
        if key in seen:
            return False
        seen.add(key)

        existing = await self._sources.get_by_external_id(
            source.platform, source.external_id
        )
        if existing is not None:
            return False

        try:
            await self._sources.add(source)
        except AlreadyExistsError:
            # Lost a race against a concurrent insert; treat as skipped.
            return False
        return True
