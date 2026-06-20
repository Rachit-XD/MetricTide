"""Deterministic trend scoring.

Combines four normalized signals into a ``trend_score`` in [0, 100]:

* **mentions** — log-normalized mention count (dampens outliers)
* **engagement** — log-normalized sum of source scores
* **diversity** — platform_count / max_platforms (linear)
* **recency** — half-life decay on the most recent source timestamp

Weights are normalized by their sum, so the score is always bounded regardless
of the configured weights. No randomness, no LLMs — same inputs, same output.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from app.domain.repositories.trend_metrics_repository import TopicMetrics


@dataclass(frozen=True, slots=True)
class ScoreWeights:
    mentions: float = 0.40
    engagement: float = 0.30
    diversity: float = 0.15
    recency: float = 0.15


@dataclass(frozen=True, slots=True)
class ScoringContext:
    """Batch-level normalization context shared across all topics in a run."""

    max_mention_count: int
    max_engagement: float
    max_platforms: int
    reference_time: datetime
    recency_half_life_hours: float


def _log_norm(value: float, maximum: float) -> float:
    if maximum <= 0:
        return 0.0
    return math.log1p(max(value, 0.0)) / math.log1p(maximum)


class TrendScoreCalculator:
    def __init__(self, weights: ScoreWeights | None = None) -> None:
        self._weights = weights or ScoreWeights()

    def score(self, metrics: TopicMetrics, ctx: ScoringContext) -> float:
        mentions_n = _log_norm(metrics.mention_count, ctx.max_mention_count)
        engagement_n = _log_norm(metrics.engagement_score, ctx.max_engagement)
        diversity_n = (
            metrics.platform_count / ctx.max_platforms if ctx.max_platforms > 0 else 0.0
        )
        recency_n = self._recency(metrics.latest_source_at, ctx)

        w = self._weights
        weighted = (
            w.mentions * mentions_n
            + w.engagement * engagement_n
            + w.diversity * diversity_n
            + w.recency * recency_n
        )
        total_weight = w.mentions + w.engagement + w.diversity + w.recency
        raw = weighted / total_weight if total_weight > 0 else 0.0
        return round(raw * 100.0, 2)

    @staticmethod
    def _recency(latest: datetime | None, ctx: ScoringContext) -> float:
        if latest is None or ctx.recency_half_life_hours <= 0:
            return 0.0
        age_hours = (ctx.reference_time - latest).total_seconds() / 3600.0
        if age_hours <= 0:
            return 1.0
        # `float ** float` is typed as Any in typeshed; make the float explicit.
        return float(0.5 ** (age_hours / ctx.recency_half_life_hours))
