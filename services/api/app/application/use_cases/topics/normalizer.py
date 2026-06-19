"""Topic normalization.

Maps raw extracted surface forms to canonical topic names and filters obvious
noise. This is a deliberately small, rule-based first pass:

* whitespace/case cleanup
* an explicit alias map ("Open AI" -> "OpenAI", "Large Language Models" -> "LLM")
* basic junk filtering (too short, all digits)

Richer alias/synonym handling (e.g. learned mappings) comes later; the alias map
is the seam for it.
"""

from __future__ import annotations

# Casefolded surface form -> canonical display name.
_ALIASES: dict[str, str] = {
    "open ai": "OpenAI",
    "openai": "OpenAI",
    "chatgpt": "ChatGPT",
    "gpt": "GPT",
    "ai": "AI",
    "a.i.": "AI",
    "artificial intelligence": "AI",
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "llm": "LLM",
    "llms": "LLM",
    "large language model": "LLM",
    "large language models": "LLM",
    "genai": "Generative AI",
    "generative ai": "Generative AI",
    "github": "GitHub",
    "google": "Google",
    "microsoft": "Microsoft",
}

# Casefolded forms that are never useful as topics.
_STOPWORDS: frozenset[str] = frozenset(
    {"show hn", "ask hn", "hn", "the", "a", "an", "new", "using", "use"}
)

_MIN_LENGTH = 2


class TopicNormalizer:
    """Normalize raw topic strings into canonical names (or ``None`` to drop)."""

    def normalize(self, raw: str) -> str | None:
        cleaned = " ".join(raw.split()).strip()
        if len(cleaned) < _MIN_LENGTH:
            return None

        key = cleaned.casefold()
        if key in _ALIASES:
            return _ALIASES[key]
        if key in _STOPWORDS:
            return None
        if cleaned.replace(".", "").replace(",", "").isdigit():
            return None
        return cleaned
