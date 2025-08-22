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

        # Always get AI evaluation for draft and rationale
        ai_result = self.decision.evaluate(profile, criteria)

        if s.value <= self.red_flag_floor or s.value < self.threshold:
            # Use AI draft but override decision to NO
            return {
                "decision": "NO",
                "rationale": f"Below threshold ({s.value:.2f} < {self.threshold})",
                "draft": ai_result.get("draft", ""),  # Keep AI-generated draft
                "score": s.value,
                "ai_decision": ai_result.get("decision"),  # Track what AI would have said
                "ai_rationale": ai_result.get("rationale", "")
            }

        # Above threshold - use full AI result with score added
        ai_result["score"] = s.value
        return ai_result
