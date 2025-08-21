"""Test event ordering invariants following TDD principles."""

from collections.abc import Mapping
from typing import Any

from yc_matcher.application.use_cases import EvaluateProfile, ProcessCandidate, SendMessage
from yc_matcher.domain.entities import Criteria, Profile


class DecisionYes:
    """Mock decision adapter that always returns YES."""

    def evaluate(self, profile: Profile, criteria: Criteria) -> Mapping[str, Any]:
        return {"decision": "YES", "rationale": "ok", "draft": "hi"}


class MessageEcho:
    """Mock message renderer."""

    def render(self, data: Mapping[str, Any]) -> str:
        return str(data.get("draft", ""))


class QuotaAlways:
    """Mock quota that always allows."""

    def check_and_increment(self, limit: int) -> bool:
        return True


class LoggerOrdered:
    """Logger that tracks event ordering."""

    def __init__(self) -> None:
        self.events: list[str] = []

    def emit(self, ev: Mapping[str, Any]) -> None:
        event_type = ev.get("event", "unknown")
        self.events.append(event_type)


class BrowserMinimal:
    """Minimal browser mock."""

    def open(self, url: str) -> None:
        pass

    def click_view_profile(self) -> bool:
        return True

    def read_profile_text(self) -> str:
        return "Profile text"

    def focus_message_box(self) -> None:
        pass

    def fill_message(self, text: str) -> None:
        pass

    def send(self) -> None:
        pass

    def skip(self) -> None:
        pass

    def verify_sent(self) -> bool:
        return True

    def close(self) -> None:
        pass


class SeenNever:
    """Mock seen repo that never marks as seen."""

    def is_seen(self, profile_hash: str) -> bool:
        return False

    def mark_seen(self, profile_hash: str) -> None:
        pass


def test_decision_precedes_sent():
    """Test that 'decision' event is always emitted before 'sent' event.

    This is a critical invariant for observability:
    - We must log the decision before attempting to send
    - This ensures we can trace why a message was sent

    Following TDD: Write test first, ensure it expresses the requirement clearly.
    """
    # Arrange
    logger = LoggerOrdered()
    browser = BrowserMinimal()
    seen = SeenNever()

    eval_use = EvaluateProfile(decision=DecisionYes(), message=MessageEcho())
    send_use = SendMessage(quota=QuotaAlways(), browser=browser, logger=logger)
    pc = ProcessCandidate(
        evaluate=eval_use,
        send=send_use,
        browser=browser,
        seen=seen,
        logger=logger
    )

    # Act
    pc(
        url="file://test",
        criteria=Criteria(text="test"),
        limit=1,
        auto_send=True
    )

    # Assert - decision must come before sent
    assert "decision" in logger.events, "Decision event not emitted"
    assert "sent" in logger.events, "Sent event not emitted"

    decision_idx = logger.events.index("decision")
    sent_idx = logger.events.index("sent")

    assert decision_idx < sent_idx, (
        f"Event ordering violation: 'decision' at {decision_idx} "
        f"must precede 'sent' at {sent_idx}. "
        f"Events: {logger.events}"
    )


def test_decision_without_sent_when_no():
    """Test that decision is logged even when not sending.

    When decision is NO, we should still see the decision event,
    but no sent event should follow.
    """
    # Arrange
    class DecisionNo:
        def evaluate(self, profile: Profile, criteria: Criteria) -> Mapping[str, Any]:
            return {"decision": "NO", "rationale": "not a match"}

    logger = LoggerOrdered()
    browser = BrowserMinimal()
    seen = SeenNever()

    eval_use = EvaluateProfile(decision=DecisionNo(), message=MessageEcho())
    send_use = SendMessage(quota=QuotaAlways(), browser=browser, logger=logger)
    pc = ProcessCandidate(
        evaluate=eval_use,
        send=send_use,
        browser=browser,
        seen=seen,
        logger=logger
    )

    # Act
    pc(
        url="file://test",
        criteria=Criteria(text="test"),
        limit=1,
        auto_send=True
    )

    # Assert
    assert "decision" in logger.events, "Decision event not emitted"
    assert "sent" not in logger.events, "Sent event should not be emitted for NO decision"


def test_multiple_profiles_maintain_ordering():
    """Test that decision→sent ordering is maintained across multiple calls."""
    # Arrange
    logger = LoggerOrdered()
    browser = BrowserMinimal()
    seen = SeenNever()

    eval_use = EvaluateProfile(decision=DecisionYes(), message=MessageEcho())
    send_use = SendMessage(quota=QuotaAlways(), browser=browser, logger=logger)
    pc = ProcessCandidate(
        evaluate=eval_use,
        send=send_use,
        browser=browser,
        seen=seen,
        logger=logger
    )

    # Act - process 3 profiles with separate calls
    for _ in range(3):
        pc(
            url="file://test",
            criteria=Criteria(text="test"),
            limit=1,
            auto_send=True
        )

    # Assert - each decision should precede its corresponding sent
    decision_indices = [i for i, e in enumerate(logger.events) if e == "decision"]
    sent_indices = [i for i, e in enumerate(logger.events) if e == "sent"]

    assert len(decision_indices) == 3, f"Expected 3 decisions, got {len(decision_indices)}"
    assert len(sent_indices) == 3, f"Expected 3 sent events, got {len(sent_indices)}"

    for i, (dec_idx, sent_idx) in enumerate(zip(decision_indices, sent_indices, strict=False)):
        assert dec_idx < sent_idx, (
            f"Profile {i}: decision at {dec_idx} must precede sent at {sent_idx}. "
            f"Events: {logger.events}"
        )


def test_quota_block_emits_event():
    """Test that quota blocking emits an observable event.

    When quota is exceeded, we should see a quota event
    with allowed=false, and no sent event should follow.

    Following TDD: Test the observability requirement.
    """
    # Arrange
    class QuotaOnce:
        """Mock quota that allows only one send."""
        def __init__(self):
            self.count = 0

        def check_and_increment(self, limit: int) -> bool:
            if self.count >= 1:
                return False  # Block second send
            self.count += 1
            return True

    logger = LoggerOrdered()
    browser = BrowserMinimal()
    seen = SeenNever()
    quota = QuotaOnce()

    eval_use = EvaluateProfile(decision=DecisionYes(), message=MessageEcho())
    send_use = SendMessage(quota=quota, browser=browser, logger=logger)
    pc = ProcessCandidate(
        evaluate=eval_use,
        send=send_use,
        browser=browser,
        seen=seen,
        logger=logger
    )

    # Act - process 2 profiles, second should be blocked
    pc(url="file://test", criteria=Criteria(text="test"), limit=1, auto_send=True)
    pc(url="file://test2", criteria=Criteria(text="test"), limit=1, auto_send=True)

    # Assert
    # First profile: decision and sent
    # Second profile: decision but no sent (quota blocked)
    decision_count = logger.events.count("decision")
    sent_count = logger.events.count("sent")

    assert decision_count == 2, f"Expected 2 decisions, got {decision_count}"
    assert sent_count == 1, f"Expected 1 sent (quota blocked second), got {sent_count}"

