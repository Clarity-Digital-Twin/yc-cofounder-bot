from collections.abc import Mapping
from typing import Any

from yc_matcher.application.use_cases import EvaluateProfile, ProcessCandidate, SendMessage
from yc_matcher.domain.entities import Criteria, Profile


class DecisionYes:
    def evaluate(self, profile: Profile, criteria: Criteria) -> Mapping[str, Any]:
        return {"decision": "YES", "rationale": "ok", "extracted": {"name": "A"}, "draft": "hi"}


class DecisionNo:
    def evaluate(self, profile: Profile, criteria: Criteria) -> Mapping[str, Any]:
        return {"decision": "NO", "rationale": "no"}


class MessageEcho:
    def render(self, data: Mapping[str, Any]) -> str:
        return str(data.get("draft", ""))


class QuotaAlways:
    def check_and_increment(self, limit: int) -> bool:  # type: ignore[no-redef]
        return True


class LoggerList:
    def __init__(self) -> None:
        self.events: list[Mapping[str, Any]] = []

    def emit(self, ev: Mapping[str, Any]) -> None:
        self.events.append(ev)


class BrowserOk:
    def __init__(self) -> None:
        self.actions: list[str] = []

    def open(self, url: str) -> None:
        self.actions.append("open")

    def click_view_profile(self) -> bool:
        self.actions.append("click_view_profile")
        return True

    def read_profile_text(self) -> str:
        return "John Doe\nProfile bio text"

    def focus_message_box(self) -> None:
        self.actions.append("focus")

    def fill_message(self, text: str) -> None:
        self.actions.append("fill")

    def send(self) -> None:
        self.actions.append("send")

    def verify_sent(self) -> bool:
        return True

    def skip(self) -> None:
        self.actions.append("skip")

    def close(self) -> None:
        self.actions.append("close")


class SeenMem:
    def __init__(self) -> None:
        self._seen: set[str] = set()

    def is_seen(self, h: str) -> bool:
        return h in self._seen

    def mark_seen(self, h: str) -> None:
        self._seen.add(h)


def test_process_candidate_skips_if_seen():
    seen = SeenMem()
    # mark hash of our profile text
    # We'll rely on ProcessCandidate to hash consistently; this test just ensures skip path
    browser = BrowserOk()
    log = LoggerList()
    eval_use = EvaluateProfile(decision=DecisionYes(), message=MessageEcho())
    send_use = SendMessage(quota=QuotaAlways(), browser=browser, logger=log)
    pc = ProcessCandidate(evaluate=eval_use, send=send_use, browser=browser, seen=seen, logger=log)

    # First run to mark seen
    pc(url="file://stub", criteria=Criteria(text=""), limit=5, auto_send=False)
    # Second run should call skip
    pc(url="file://stub", criteria=Criteria(text=""), limit=5, auto_send=False)
    assert "skip" in browser.actions


def test_process_candidate_auto_send_on_yes():
    seen = SeenMem()
    browser = BrowserOk()
    log = LoggerList()
    eval_use = EvaluateProfile(decision=DecisionYes(), message=MessageEcho())
    send_use = SendMessage(quota=QuotaAlways(), browser=browser, logger=log)
    pc = ProcessCandidate(evaluate=eval_use, send=send_use, browser=browser, seen=seen, logger=log)

    pc(url="file://stub", criteria=Criteria(text=""), limit=5, auto_send=True)
    # Ensure send path happened
    assert "send" in browser.actions
    kinds = [e.get("event") for e in log.events]
    assert "sent" in kinds


def test_process_candidate_no_send_when_no():
    seen = SeenMem()
    browser = BrowserOk()
    log = LoggerList()
    eval_use = EvaluateProfile(decision=DecisionNo(), message=MessageEcho())
    send_use = SendMessage(quota=QuotaAlways(), browser=browser, logger=log)
    pc = ProcessCandidate(evaluate=eval_use, send=send_use, browser=browser, seen=seen, logger=log)

    pc(url="file://stub", criteria=Criteria(text=""), limit=5, auto_send=True)
    assert "send" not in browser.actions
