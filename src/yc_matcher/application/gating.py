from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any

from ..domain.entities import Criteria, Profile
from .ports import DecisionPort, MessagePort, ScoringPort


@dataclass
class GatedDecision:
    scoring: ScoringPort
    decision: DecisionPort
    message: MessagePort
    threshold: float = 4.0
    red_flag_floor: float = -100.0

    def __call__(self, profile: Profile, criteria: Criteria) -> Mapping[str, Any]:
        s = self.scoring.score(profile, criteria)
        if s.value <= self.red_flag_floor or s.value < self.threshold:
            # Fail-closed NO with minimal payload
            return {"decision": "NO", "rationale": "Below threshold or red flags", "draft": ""}
        data = self.decision.evaluate(profile, criteria)
        draft = self.message.render(data)
        return {**data, "draft": draft}

