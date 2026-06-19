"""Local topic extraction using spaCy NER + KeyBERT keyphrases.

Combines two signals into candidate topics:

* **spaCy named entities** (ORG, PERSON, PRODUCT, ...) — e.g. "OpenAI",
  "Noam Shazeer". Assigned a fixed confidence (the small English model does not
  expose per-entity probabilities).
* **KeyBERT keyphrases** — e.g. "AI", "machine learning". Confidence is the
  cosine similarity KeyBERT returns.

Heavy models (spaCy pipeline + sentence-transformer) load once when this object
is constructed, so it is built as a process-wide singleton. No external APIs.
"""

from __future__ import annotations

from app.application.ports.topic_extraction import ExtractedTopic, TopicExtractionPort
from app.core.logging import get_logger

logger = get_logger(__name__)

# Named-entity labels that make useful topics.
_ENTITY_LABELS = frozenset(
    {"ORG", "PERSON", "PRODUCT", "GPE", "NORP", "EVENT", "WORK_OF_ART", "FAC", "LOC", "LANGUAGE"}
)


class SpacyKeyBertTopicExtractor(TopicExtractionPort):
    def __init__(
        self,
        spacy_model: str = "en_core_web_sm",
        embedding_model: str = "all-MiniLM-L6-v2",
        top_n: int = 5,
        ner_confidence: float = 0.8,
    ) -> None:
        import spacy
        from keybert import KeyBERT
        from sentence_transformers import SentenceTransformer

        logger.info("nlp.loading_models", spacy_model=spacy_model, embedding_model=embedding_model)
        self._nlp = spacy.load(spacy_model)
        self._embedder = SentenceTransformer(embedding_model)
        self._keybert = KeyBERT(model=self._embedder)
        self._top_n = top_n
        self._ner_confidence = ner_confidence
        logger.info("nlp.models_loaded")

    def extract(self, text: str) -> list[ExtractedTopic]:
        text = (text or "").strip()
        if not text:
            return []

        scores: dict[str, float] = {}

        # Named entities.
        for ent in self._nlp(text).ents:
            if ent.label_ not in _ENTITY_LABELS:
                continue
            name = ent.text.strip()
            if name:
                scores[name] = max(scores.get(name, 0.0), self._ner_confidence)

        # KeyBERT keyphrases.
        try:
            keywords = self._keybert.extract_keywords(
                text,
                keyphrase_ngram_range=(1, 2),
                stop_words="english",
                top_n=self._top_n,
            )
        except Exception:
            logger.warning("nlp.keybert_failed", exc_info=True)
            keywords = []

        for phrase, score in keywords:
            name = phrase.strip()
            if name:
                scores[name] = max(scores.get(name, 0.0), float(score))

        return [
            ExtractedTopic(name=name, confidence=min(max(conf, 0.0), 1.0))
            for name, conf in scores.items()
        ]
