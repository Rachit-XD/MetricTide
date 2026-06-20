"""Embedding port.

Abstracts text -> vector so the embedding model (sentence-transformers) stays in
infrastructure and can be faked in tests. Embedding is CPU-bound and synchronous;
callers run it off the event loop (e.g. via ``asyncio.to_thread``).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingPort(ABC):
    """Contract for turning text into dense vectors."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensionality of the produced vectors."""

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding per input text (order preserved)."""
