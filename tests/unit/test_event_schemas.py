"""Test event schemas are consistent across the application."""

from unittest.mock import Mock

from yc_matcher.application.use_cases import SendMessage


class TestEventSchemas:
    """Ensure event schemas are consistent for observability."""

    def test_quota_event_schema_consistency(self) -> None:
        """Test quota events always have consistent schema."""
        # Expected schema
        # expected_keys = {"event", "allowed", "limit", "day_count", "week_count"}

        # Arrange - mock logger to capture events
        events = []
        mock_logger = Mock()
        mock_logger.emit = Mock(side_effect=lambda e: events.append(e))

        mock_browser = Mock()
        mock_browser.focus_message_box = Mock()
        mock_browser.fill_message = Mock()
        mock_browser.send = Mock()
        mock_browser.verify_sent = Mock(return_value=True)

        # Mock quota that will block
        mock_quota = Mock()
        mock_quota.check_and_increment = Mock(return_value=False)

        send_use_case = SendMessage(
            quota=mock_quota, browser=mock_browser, logger=mock_logger, stop=None
        )

        # Act - try to send (should be blocked by quota)
        _ = send_use_case("Test message", limit=10)

        # Assert - find quota event
        quota_events = [e for e in events if e.get("event") == "quota_block"]
        assert len(quota_events) > 0, "Should emit quota event when blocked"

        # Check it has expected shape
        quota_event = quota_events[0]
        assert "limit" in quota_event, "Quota event must include limit"

    def test_sent_event_schema(self) -> None:
        """Test sent events have consistent schema."""
        # Expected schema for sent event
        expected_keys = {"event", "ok", "mode", "verified"}

        # Arrange
        events = []
        mock_logger = Mock()
        mock_logger.emit = Mock(side_effect=lambda e: events.append(e))

        mock_browser = Mock()
        mock_browser.focus_message_box = Mock()
        mock_browser.fill_message = Mock()
        mock_browser.send = Mock()
        mock_browser.verify_sent = Mock(return_value=True)

        mock_quota = Mock()
        mock_quota.check_and_increment = Mock(return_value=True)

        send_use_case = SendMessage(
            quota=mock_quota, browser=mock_browser, logger=mock_logger, stop=None
        )

        # Act - send successfully
        _ = send_use_case("Test message", limit=10)

        # Assert - find sent event
        sent_events = [e for e in events if e.get("event") == "sent"]
        assert len(sent_events) > 0, "Should emit sent event"

        sent_event = sent_events[0]
        for key in expected_keys:
            assert key in sent_event, f"Sent event must include '{key}'"
        assert sent_event["ok"] is True
        assert sent_event["mode"] == "auto"
        assert sent_event["verified"] is True

    def test_stopped_event_schema(self) -> None:
        """Test stopped events include location context."""
        # Arrange
        events = []
        mock_logger = Mock()
        mock_logger.emit = Mock(side_effect=lambda e: events.append(e))

        mock_browser = Mock()
        mock_quota = Mock()

        mock_stop = Mock()
        mock_stop.is_stopped = Mock(return_value=True)

        send_use_case = SendMessage(
            quota=mock_quota, browser=mock_browser, logger=mock_logger, stop=mock_stop
        )

        # Act - try to send (should be stopped immediately)
        _ = send_use_case("Test", 10)

        # Assert
        stopped_events = [e for e in events if e.get("event") == "stopped"]
        assert len(stopped_events) > 0, "Should emit stopped event"

        stopped_event = stopped_events[0]
        assert "where" in stopped_event, "Stopped event must include 'where' context"
        assert stopped_event["where"] in {
            "send_message_start",
            "before_focus",
            "after_focus",
            "before_send",
            "before_retry",
        }

    def test_no_sent_after_quota_block(self) -> None:
        """Test that no sent event follows a quota block in same call."""
        # Arrange
        events = []
        mock_logger = Mock()
        mock_logger.emit = Mock(side_effect=lambda e: events.append(e))

        mock_browser = Mock()
        mock_quota = Mock()
        mock_quota.check_and_increment = Mock(return_value=False)  # Block

        send_use_case = SendMessage(
            quota=mock_quota, browser=mock_browser, logger=mock_logger, stop=None
        )

        # Act
        result = send_use_case("Test", 10)

        # Assert
        assert result is False, "Should return False when quota blocked"

        # Check no sent event after quota_block
        quota_idx = None
        for i, e in enumerate(events):
            if e.get("event") == "quota_block":
                quota_idx = i
                break

        if quota_idx is not None:
            # No sent events should follow
            for e in events[quota_idx + 1 :]:
                assert e.get("event") != "sent", (
                    "No sent event should follow quota_block in same call"
                )
