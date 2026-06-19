"""Small time helpers shared across ingestion sources."""

from __future__ import annotations

from datetime import UTC, datetime


def epoch_to_utc(epoch: int | float | None) -> datetime | None:
    """Convert Unix epoch seconds to a timezone-aware UTC datetime.

    Returns ``None`` for ``None`` input so callers can pass through optional
    timestamps unchanged.
    """
    if epoch is None:
        return None
    return datetime.fromtimestamp(epoch, tz=UTC)
