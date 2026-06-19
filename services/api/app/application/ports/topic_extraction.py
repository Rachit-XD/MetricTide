"""Topic extraction port.

Abstracts "given text, return candidate topics with confidence" so the
extraction implementation (spaCy + KeyBERT) stays in infrastructure and can be
faked in tests. Extraction is CPU-bound and synchronous; callers run it off the
event loop (e.g. via ``asyncio.to_thread``).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExtractedTopic:
    """A raw (pre-normalization) candidate topic and its confidence in [0, 1]."""

    name: str
    confidence: float


class TopicExtractionPort(ABC):
    """Contract for extracting candidate topics from text."""

    @abstractmethod
    def extract(self, text: str) -> list[ExtractedTopic]:
        """Return candidate topics for ``text`` (may be empty)."""
