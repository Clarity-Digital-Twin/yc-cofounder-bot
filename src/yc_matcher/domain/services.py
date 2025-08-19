from __future__ import annotations

from .entities import Criteria, Profile, Score


class ScoringService:
    """Deterministic scoring for transparency (Strategy-friendly).

    Replace/extend with weighted rules. Keep pure (no I/O).
    """

    def score(self, profile: Profile, criteria: Criteria) -> Score:
        text = profile.raw_text.lower()
        keys = criteria.keywords or [
            k.strip() for k in criteria.text.replace("\n", ",").split(",") if k.strip()
        ]
        reasons: list[str] = []
        hits = 0
        for k in keys:
            if k and k.lower() in text:
                hits += 1
                reasons.append(f"keyword:{k}")
        value = float(hits)
        return Score(value=value, reasons=reasons)


class WeightedScoringService:
    """Keyword-weighted scoring.

    weights: mapping from lowercase token -> weight (positive or negative).
    """

    def __init__(self, weights: dict[str, float]):
        self.weights = {k.lower(): float(v) for k, v in weights.items()}

    def score(self, profile: Profile, criteria: Criteria) -> Score:
        text = profile.raw_text.lower()
        reasons: list[str] = []
        total = 0.0
        tokens = set(self.weights.keys())
        for token in tokens:
            if token and token in text:
                w = self.weights[token]
                total += w
                reasons.append(f"kw:{token}:{w}")
        return Score(value=total, reasons=reasons)
