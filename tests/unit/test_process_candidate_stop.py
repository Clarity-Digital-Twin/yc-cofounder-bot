from yc_matcher.application.use_cases import EvaluateProfile, ProcessCandidate, SendMessage
from yc_matcher.domain.entities import Criteria, Profile


class DecisionYes:
    def evaluate(self, profile: Profile, criteria: Criteria):
        return {"decision": "YES", "rationale": "ok", "draft": "hi"}


class QuotaOk:
    def check_and_increment(self, limit: int) -> bool:  # type: ignore[no-redef]
        return True


class LoggerList:
    def __init__(self) -> None:
        self.events = []

    def emit(self, ev):
        self.events.append(ev)


class BrowserSpy:
    def __init__(self) -> None:
        self.sent = False

    def open(self, url: str) -> None: ...
    def click_view_profile(self) -> bool:
        return True

    def read_profile_text(self) -> str:
        return "John Doe"

    def focus_message_box(self) -> None: ...
    def fill_message(self, text: str) -> None: ...
    def send(self) -> None:
        self.sent = True

    def verify_sent(self) -> bool:
        return True

    def skip(self) -> None: ...
    def close(self) -> None: ...


class StopTrue:
    def is_stopped(self) -> bool:
        return True


def test_process_respects_stop_before_navigate():
    eval_use = EvaluateProfile(decision=DecisionYes(), message=lambda d: d.get("draft", ""))
    log = LoggerList()
    b = BrowserSpy()
    send = SendMessage(quota=QuotaOk(), browser=b, logger=log)
    pc = ProcessCandidate(
        evaluate=eval_use,
        send=send,
        browser=b,
        seen=type("S", (), {"is_seen": lambda *_: False, "mark_seen": lambda *_: None})(),
        logger=log,
        stop=StopTrue(),
    )
    pc(url="file://stub", criteria=Criteria(text=""), limit=5, auto_send=True)
    assert b.sent is False
    kinds = [e.get("event") for e in log.events]
    assert "stopped" in kinds
