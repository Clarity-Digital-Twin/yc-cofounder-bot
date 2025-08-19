from collections.abc import Mapping
from typing import Any

from yc_matcher.application.use_cases import EvaluateProfile, SendMessage
from yc_matcher.domain.entities import Criteria, Profile


class DecisionMock:
    def evaluate(self, profile: Profile, criteria: Criteria) -> Mapping[str, Any]:
        return {"decision": "YES", "rationale": "fits", "extracted": {"name": "Alex"}}


class MessageMock:
    def render(self, decision: Mapping[str, Any]) -> str:
        return f"Hello {decision.get('extracted', {}).get('name', 'there')}"


def test_evaluate_profile_combines_decision_and_draft():
    use = EvaluateProfile(decision=DecisionMock(), message=MessageMock())
    out = use(Profile(raw_text=""), Criteria(text=""))
    assert out["decision"] == "YES"
    assert out["draft"].startswith("Hello ")


class QuotaMock:
    def __init__(self):
        self.calls = 0

    def check_and_increment(self, limit: int) -> bool:
        self.calls += 1
        return self.calls == 1  # allow once, then block


class BrowserMock:
    def __init__(self):
        self.actions = []

    def focus_message_box(self) -> None:
        self.actions.append("focus")

    def fill_message(self, text: str) -> None:
        self.actions.append(("fill", text))

    def send(self) -> None:
        self.actions.append("send")


class LoggerMock:
    def __init__(self):
        self.events = []

    def emit(self, ev: Mapping[str, Any]) -> None:
        self.events.append(ev)


def test_send_message_respects_quota_and_calls_browser():
    q = QuotaMock()
    b = BrowserMock()
    log = LoggerMock()
    use = SendMessage(quota=q, browser=b, logger=log)
    ok = use("hi", limit=1)
    assert ok is True
    assert "send" in b.actions

    ok2 = use("hi again", limit=1)
    assert ok2 is False
    assert any(e.get("event") == "quota_block" for e in log.events)
