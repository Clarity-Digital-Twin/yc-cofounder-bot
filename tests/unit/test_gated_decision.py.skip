from collections.abc import Mapping
from typing import Any

from yc_matcher.application.gating import GatedDecision
from yc_matcher.domain.entities import Criteria, Profile
from yc_matcher.domain.services import WeightedScoringService


class DecisionMock:
    def evaluate(self, profile: Profile, criteria: Criteria) -> Mapping[str, Any]:
        return {"decision": "YES", "rationale": "fits", "extracted": {"name": "Sam"}}


def test_gated_decision_blocks_below_threshold():
    scoring = WeightedScoringService(weights={"python": 3})
    gate = GatedDecision(scoring=scoring, decision=DecisionMock(), threshold=4.0)
    out = gate.evaluate(Profile(raw_text="python"), Criteria(text="python"))
    assert out["decision"] == "NO"
    assert out.get("draft", "") == ""


def test_gated_decision_allows_at_threshold_and_above():
    scoring = WeightedScoringService(weights={"python": 3, "fastapi": 2})
    gate = GatedDecision(scoring=scoring, decision=DecisionMock(), threshold=4.0)
    out = gate.evaluate(Profile(raw_text="python and fastapi"), Criteria(text="python,fastapi"))
    assert out["decision"] == "YES"


def test_gated_decision_blocks_red_flags():
    scoring = WeightedScoringService(weights={"python": 3, "crypto": -999})
    gate = GatedDecision(scoring=scoring, decision=DecisionMock(), red_flag_floor=-100)
    out = gate.evaluate(Profile(raw_text="python with crypto"), Criteria(text="python,crypto"))
    assert out["decision"] == "NO"
    assert out.get("draft", "") == ""
