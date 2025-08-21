from collections.abc import Mapping
from typing import Any

from yc_matcher.application.use_cases import SendMessage


class QuotaAllowOnce:
    def __init__(self) -> None:
        self.calls = 0

    def check_and_increment(self, limit: int) -> bool:  # type: ignore[no-redef]
        self.calls += 1
        return True


class LoggerCapture:
    def __init__(self) -> None:
        self.events: list[Mapping[str, Any]] = []

    def emit(self, ev: Mapping[str, Any]) -> None:
        self.events.append(ev)


class BrowserMock:
    def __init__(self, first_ok: bool, second_ok: bool) -> None:
        self.first_ok = first_ok
        self.second_ok = second_ok
        self.sends = 0
        self.filled: list[str] = []

    def focus_message_box(self) -> None:
        pass

    def fill_message(self, text: str) -> None:
        self.filled.append(text)

    def send(self) -> None:
        self.sends += 1

    def verify_sent(self) -> bool:
        return self.first_ok if self.sends == 1 else self.second_ok

    # Unused in this test
    def open(self, url: str) -> None:  # pragma: no cover
        pass

    def click_view_profile(self) -> bool:  # pragma: no cover
        return True

    def read_profile_text(self) -> str:  # pragma: no cover
        return ""

    def skip(self) -> None:  # pragma: no cover
        pass

    def close(self) -> None:  # pragma: no cover
        pass


def test_send_message_verifies_and_retries_once_then_succeeds():
    quota = QuotaAllowOnce()
    browser = BrowserMock(first_ok=False, second_ok=True)
    log = LoggerCapture()
    use = SendMessage(quota=quota, browser=browser, logger=log)
    ok = use("hello", limit=5)
    assert ok is True
    # At least one verify_failed then sent with retry
    kinds = [e.get("event") for e in log.events]
    assert "verify_failed" in kinds
    assert "sent" in kinds


def test_send_message_fails_after_retry():
    quota = QuotaAllowOnce()
    browser = BrowserMock(first_ok=False, second_ok=False)
    log = LoggerCapture()
    use = SendMessage(quota=quota, browser=browser, logger=log)
    ok = use("hello", limit=5)
    assert ok is False
    kinds = [e.get("event") for e in log.events]
    assert "send_failed" in kinds
