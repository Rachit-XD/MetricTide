"""Embedding implementation backed by sentence-transformers (all-MiniLM-L6-v2).

Produces 384-dimensional vectors on CPU. The model loads once on construction,
so this is built as a process-wide singleton. No external APIs.
"""

from __future__ import annotations

from app.application.ports.embedding import EmbeddingPort
from app.core.logging import get_logger

logger = get_logger(__name__)


class SentenceTransformerEmbedder(EmbeddingPort):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", batch_size: int = 64) -> None:
        from sentence_transformers import SentenceTransformer

        logger.info("embedding.loading_model", model=model_name)
        self._model = SentenceTransformer(model_name)
        self._batch_size = batch_size
        self._dimension = int(self._model.get_sentence_embedding_dimension())
        logger.info("embedding.model_loaded", model=model_name, dimension=self._dimension)

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(
            texts,
            batch_size=self._batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return [vector.tolist() for vector in vectors]
