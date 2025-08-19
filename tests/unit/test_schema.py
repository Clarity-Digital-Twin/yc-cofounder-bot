from yc_matcher.application.schema import DecisionDTO, Extracted
import pytest


def test_decision_literal_yes_no_only():
    ok = DecisionDTO(decision="YES", rationale="ok", draft="", extracted=Extracted())
    assert ok.decision == "YES"
    with pytest.raises(Exception):
        DecisionDTO(decision="MAYBE", rationale="x", draft="")

