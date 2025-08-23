"""Happy path test for autonomous flow."""

from unittest.mock import Mock

from yc_matcher.application.autonomous_flow import AutonomousFlow


class TestAutonomousFlowHappyPath:
    """Test the complete happy path: evaluate -> decide YES -> send."""

    def test_happy_path_evaluate_decide_send(self) -> None:
        """Profile evaluated as YES with auto_send should result in message sent."""
        # Arrange
        browser = Mock()
        browser.open = Mock()
        browser.click_view_profile = Mock(return_value=True)
        browser.read_profile_text = Mock(return_value="Perfect match profile")
        browser.skip = Mock()

        # Evaluation returns YES with auto_send
        evaluate = Mock(return_value={
            "decision": "YES",
            "rationale": "Perfect technical match",
            "draft": "Hi! I'd love to connect.",
            "auto_send": True,
            "score": 0.95,
            "confidence": 0.9,
        })

        # Send succeeds
        send = Mock(return_value=True)

        # Not a duplicate
        seen = Mock()
        seen.is_seen = Mock(return_value=False)
        seen.mark_seen = Mock()

        # Collect events for verification
        events = []
        logger = Mock()
        logger.emit = Mock(side_effect=lambda e: events.append(e))

        # No stop flag
        stop = Mock()
        stop.is_stopped = Mock(return_value=False)

        # Quota allows
        quota = Mock()

        flow = AutonomousFlow(browser, evaluate, send, seen, logger, stop, quota)

        # Act
        results = flow.run(
            your_profile="Technical founder",
            criteria="Business co-founder",
            template="Template message",
            mode="ai",
            limit=1,
            shadow_mode=False,
        )

        # Assert - Results
        assert results["total_evaluated"] == 1
        assert results["total_sent"] == 1
        assert results["total_skipped"] == 0
        assert len(results["results"]) == 1

        result = results["results"][0]
        assert result["decision"] == "YES"
        assert result["rationale"] == "Perfect technical match"
        assert result["sent"] is True

        # Assert - Calls
        evaluate.assert_called_once()
        send.assert_called_once_with("Hi! I'd love to connect.", 1)
        seen.mark_seen.assert_called_once()

        # Assert - Event ordering (decision before sent)
        event_types = [e["event"] for e in events]
        assert "decision" in event_types
        assert "sent" in event_types

        decision_idx = event_types.index("decision")
        sent_idx = event_types.index("sent")
        assert decision_idx < sent_idx, "Decision event must come before sent event"

        # Assert - Event contents
        decision_event = next(e for e in events if e["event"] == "decision")
        assert decision_event["decision"] == "YES"
        assert decision_event["auto_send"] is True
        assert decision_event["mode"] == "ai"

        sent_event = next(e for e in events if e["event"] == "sent")
        assert sent_event["ok"] is True
        assert sent_event["mode"] == "auto"
        assert sent_event["verified"] is True

    def test_happy_path_with_multiple_profiles(self) -> None:
        """Process multiple profiles with mixed decisions."""
        # Arrange
        browser = Mock()
        browser.open = Mock()
        browser.click_view_profile = Mock(side_effect=[True, True, False])  # Stop after 2
        browser.read_profile_text = Mock(side_effect=["Profile 1", "Profile 2"])
        browser.skip = Mock()

        # First YES, second NO
        evaluate = Mock(side_effect=[
            {"decision": "YES", "draft": "Hi!", "auto_send": True, "rationale": "Good"},
            {"decision": "NO", "rationale": "Not a match"},
        ])

        send = Mock(return_value=True)
        seen = Mock()
        seen.is_seen = Mock(return_value=False)
        seen.mark_seen = Mock()

        logger = Mock()
        stop = Mock()
        stop.is_stopped = Mock(return_value=False)
        quota = Mock()

        flow = AutonomousFlow(browser, evaluate, send, seen, logger, stop, quota)

        # Act
        results = flow.run(
            your_profile="Test",
            criteria="Test",
            template="Hi",
            mode="ai",
            limit=5,
            shadow_mode=False,
        )

        # Assert
        assert results["total_evaluated"] == 2
        assert results["total_sent"] == 1  # Only first was YES
        assert len(results["results"]) == 2

        assert results["results"][0]["decision"] == "YES"
        assert results["results"][0]["sent"] is True
        assert results["results"][1]["decision"] == "NO"
        assert results["results"][1]["sent"] is False

        # Only one message sent
        send.assert_called_once_with("Hi!", 1)
