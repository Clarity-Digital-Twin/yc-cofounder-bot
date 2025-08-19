from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ..domain.entities import Criteria, Profile
from .ports import DecisionPort, ScoringPort


@dataclass
class GatedDecision:
    scoring: ScoringPort
    decision: DecisionPort
    threshold: float = 4.0
    red_flag_floor: float = -100.0

    def evaluate(self, profile: Profile, criteria: Criteria) -> Mapping[str, Any]:
        s = self.scoring.score(profile, criteria)
        if s.value <= self.red_flag_floor or s.value < self.threshold:
            # Fail-closed NO with minimal payload
            return {"decision": "NO", "rationale": "Below threshold or red flags", "draft": ""}
        return self.decision.evaluate(profile, criteria)
