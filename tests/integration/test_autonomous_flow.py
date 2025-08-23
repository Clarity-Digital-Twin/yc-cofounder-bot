"""Integration tests for autonomous flow with minimal mocks."""

from unittest.mock import Mock

from yc_matcher.application.autonomous_flow import AutonomousFlow, hash_profile_text


class TestAutonomousFlow:
    """Test autonomous browsing flow orchestrator."""

    def test_autonomous_flow_respects_limit(self) -> None:
        """Test flow processes up to limit profiles."""
        # Arrange
        browser = Mock()
        browser.open = Mock()
        browser.click_view_profile = Mock(return_value=True)
        browser.read_profile_text = Mock(
            side_effect=["Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"]
        )
        browser.skip = Mock()

        evaluate = Mock()
        evaluate.return_value = {"decision": "NO", "rationale": "Not a match"}

        send = Mock()
        send.return_value = True

        seen = Mock()
        seen.is_seen = Mock(return_value=False)
        seen.mark_seen = Mock()

        logger = Mock()
        stop = Mock()
        stop.is_stopped = Mock(return_value=False)
        quota = Mock()

        flow = AutonomousFlow(
            browser=browser,
            evaluate=evaluate,
            send=send,
            seen=seen,
            logger=logger,
            stop=stop,
            quota=quota,
        )

        # Act
        results = flow.run(
            your_profile="My profile",
            criteria="Python",
            template="Hi",
            mode="rubric",
            limit=3,  # Process only 3
            shadow_mode=False,
        )

        # Assert
        assert results["total_evaluated"] == 3
        assert browser.click_view_profile.call_count == 3
        assert browser.read_profile_text.call_count == 3

    def test_autonomous_flow_stops_on_flag(self) -> None:
        """Test flow stops immediately when stop flag is set."""
        # Arrange
        browser = Mock()
        browser.open = Mock()
        browser.click_view_profile = Mock(return_value=True)
        browser.read_profile_text = Mock(return_value="Profile")
        browser.skip = Mock()

        evaluate = Mock()
        evaluate.return_value = {"decision": "NO", "rationale": "Test"}
        send = Mock()
        seen = Mock()
        seen.is_seen = Mock(return_value=False)
        seen.mark_seen = Mock()

        logger = Mock()
        stop = Mock()
        stop.is_stopped = Mock(side_effect=[False, True])  # Stop after first
        quota = Mock()

        flow = AutonomousFlow(
            browser=browser,
            evaluate=evaluate,
            send=send,
            seen=seen,
            logger=logger,
            stop=stop,
            quota=quota,
        )

        # Act
        results = flow.run(
            your_profile="My profile",
            criteria="Python",
            template="Hi",
            mode="rubric",
            limit=10,
            shadow_mode=False,
        )

        # Assert - should stop after 1
        assert results["total_evaluated"] == 1
        logger.emit.assert_any_call({"event": "stopped", "at_profile": 1, "reason": "stop_flag"})

    def test_autonomous_flow_skips_duplicates(self) -> None:
        """Test flow skips already seen profiles."""
        # Arrange
        browser = Mock()
        browser.open = Mock()
        browser.click_view_profile = Mock(return_value=True)
        browser.read_profile_text = Mock(
            side_effect=[
                "Profile 1",
                "Profile 2",
                "Profile 1",  # Duplicate
            ]
        )
        browser.skip = Mock()

        evaluate = Mock()
        evaluate.return_value = {"decision": "NO", "rationale": "No match"}

        send = Mock()
        seen = Mock()
        seen.is_seen = Mock(side_effect=[False, False, True])  # Third is seen
        seen.mark_seen = Mock()

        logger = Mock()
        stop = Mock()
        stop.is_stopped = Mock(return_value=False)
        quota = Mock()

        flow = AutonomousFlow(
            browser=browser,
            evaluate=evaluate,
            send=send,
            seen=seen,
            logger=logger,
            stop=stop,
            quota=quota,
        )

        # Act
        results = flow.run(
            your_profile="My profile",
            criteria="Python",
            template="Hi",
            mode="rubric",
            limit=3,
            shadow_mode=False,
        )

        # Assert
        assert results["total_evaluated"] == 2  # Only 2 unique
        assert results["total_skipped"] == 1
        logger.emit.assert_any_call({"event": "duplicate", "hash": hash_profile_text("Profile 1")})

    def test_autonomous_flow_sends_on_yes(self) -> None:
        """Test flow sends message when decision is YES."""
        # Arrange
        browser = Mock()
        browser.open = Mock()
        browser.click_view_profile = Mock(return_value=True)
        browser.read_profile_text = Mock(return_value="Great profile")
        browser.skip = Mock()

        evaluate = Mock()
        evaluate.return_value = {
            "decision": "YES",
            "rationale": "Good match",
            "draft": "Hello!",
            "auto_send": True,
            "score": 5.0,  # Add score for rubric mode
        }

        send = Mock()
        send.return_value = True

        seen = Mock()
        seen.is_seen = Mock(return_value=False)
        seen.mark_seen = Mock()

        logger = Mock()
        stop = Mock()
        stop.is_stopped = Mock(return_value=False)
        quota = Mock()

        flow = AutonomousFlow(
            browser=browser,
            evaluate=evaluate,
            send=send,
            seen=seen,
            logger=logger,
            stop=stop,
            quota=quota,
        )

        # Act
        results = flow.run(
            your_profile="My profile",
            criteria="Python",
            template="Hi",
            mode="rubric",
            limit=1,
            shadow_mode=False,
            threshold=4.0,
        )

        # Assert
        assert results["total_sent"] == 1
        send.assert_called_once_with("Hello!", 1)
        logger.emit.assert_any_call(
            {"event": "sent", "profile": 0, "ok": True, "mode": "auto", "verified": True}
        )

    def test_autonomous_flow_shadow_mode_no_send(self) -> None:
        """Test shadow mode evaluates but doesn't send."""
        # Arrange
        browser = Mock()
        browser.open = Mock()
        browser.click_view_profile = Mock(return_value=True)
        browser.read_profile_text = Mock(return_value="Profile")
        browser.skip = Mock()

        evaluate = Mock()
        evaluate.return_value = {
            "decision": "YES",
            "rationale": "Good",
            "draft": "Message",
            "auto_send": True,
            "score": 5.0,  # Add score for rubric mode
        }

        send = Mock()
        seen = Mock()
        seen.is_seen = Mock(return_value=False)
        seen.mark_seen = Mock()

        logger = Mock()
        stop = Mock()
        stop.is_stopped = Mock(return_value=False)
        quota = Mock()

        flow = AutonomousFlow(
            browser=browser,
            evaluate=evaluate,
            send=send,
            seen=seen,
            logger=logger,
            stop=stop,
            quota=quota,
        )

        # Act
        results = flow.run(
            your_profile="My profile",
            criteria="Python",
            template="Hi",
            mode="rubric",
            limit=1,
            shadow_mode=True,  # Shadow mode
        )

        # Assert
        assert results["total_sent"] == 0
        send.assert_not_called()
        logger.emit.assert_any_call({"event": "shadow_send", "profile": 0, "would_send": True})

    def test_autonomous_flow_decision_event_ordering(self) -> None:
        """Test decision event always precedes sent event."""
        # Arrange
        browser = Mock()
        browser.open = Mock()
        browser.click_view_profile = Mock(return_value=True)
        browser.read_profile_text = Mock(return_value="Profile")

        evaluate = Mock()
        evaluate.return_value = {
            "decision": "YES",
            "rationale": "Good",
            "draft": "Message",
            "auto_send": True,
            "score": 5.0,  # Add score for rubric mode
        }

        send = Mock()
        send.return_value = True

        seen = Mock()
        seen.is_seen = Mock(return_value=False)
        seen.mark_seen = Mock()

        events = []
        logger = Mock()
        logger.emit = Mock(side_effect=lambda e: events.append(e["event"]))

        stop = Mock()
        stop.is_stopped = Mock(return_value=False)
        quota = Mock()

        flow = AutonomousFlow(
            browser=browser,
            evaluate=evaluate,
            send=send,
            seen=seen,
            logger=logger,
            stop=stop,
            quota=quota,
        )

        # Act
        flow.run(
            your_profile="My profile",
            criteria="Python",
            template="Hi",
            mode="rubric",
            limit=1,
            shadow_mode=False,
        )

        # Assert - decision must come before sent
        decision_idx = events.index("decision")
        sent_idx = events.index("sent")
        assert decision_idx < sent_idx

    def test_autonomous_flow_handles_errors_gracefully(self) -> None:
        """Test flow continues after profile errors."""
        # Arrange
        browser = Mock()
        browser.open = Mock()
        browser.click_view_profile = Mock(return_value=True)
        browser.read_profile_text = Mock(
            side_effect=[
                Exception("Network error"),  # First fails
                "Good profile",  # Second succeeds
            ]
        )
        browser.skip = Mock()

        evaluate = Mock()
        evaluate.return_value = {"decision": "NO", "rationale": "No"}

        send = Mock()
        seen = Mock()
        seen.is_seen = Mock(return_value=False)
        seen.mark_seen = Mock()

        logger = Mock()
        stop = Mock()
        stop.is_stopped = Mock(return_value=False)
        quota = Mock()

        flow = AutonomousFlow(
            browser=browser,
            evaluate=evaluate,
            send=send,
            seen=seen,
            logger=logger,
            stop=stop,
            quota=quota,
        )

        # Act
        results = flow.run(
            your_profile="My profile",
            criteria="Python",
            template="Hi",
            mode="rubric",
            limit=2,
            shadow_mode=False,
        )

        # Assert - should handle error and continue
        # Note: The flow may count error profiles in evaluated count
        assert results["total_evaluated"] >= 1  # At least one succeeded
        assert results["total_evaluated"] <= 2  # At most both attempts
        # Check that an error was logged (may have additional fields)
        error_calls = [call for call in logger.emit.call_args_list 
                      if call[0][0].get("event") == "error" 
                      and "Network error" in str(call[0][0].get("error", ""))]
        assert len(error_calls) > 0, "Should have logged the network error"

    def test_autonomous_flow_respects_mode_auto_send(self) -> None:
        """Test flow respects decision mode auto-send behavior."""
        # Arrange
        browser = Mock()
        browser.open = Mock()
        browser.click_view_profile = Mock(return_value=True)
        browser.read_profile_text = Mock(return_value="Profile")
        browser.skip = Mock()

        # Advisor mode - no auto send
        evaluate = Mock()
        evaluate.return_value = {
            "decision": "YES",
            "rationale": "Good",
            "draft": "Message",
            "auto_send": False,  # Advisor mode
        }

        send = Mock()
        seen = Mock()
        seen.is_seen = Mock(return_value=False)

        logger = Mock()
        stop = Mock()
        stop.is_stopped = Mock(return_value=False)
        quota = Mock()

        flow = AutonomousFlow(
            browser=browser,
            evaluate=evaluate,
            send=send,
            seen=seen,
            logger=logger,
            stop=stop,
            quota=quota,
        )

        # Act
        results = flow.run(
            your_profile="My profile",
            criteria="Python",
            template="Hi",
            mode="advisor",  # Advisor mode
            limit=1,
            shadow_mode=False,
        )

        # Assert - should not send despite YES
        assert results["total_sent"] == 0
        send.assert_not_called()


class TestHashFunction:
    """Test profile hashing for deduplication."""

    def test_hash_is_deterministic(self) -> None:
        """Test same text produces same hash."""
        text = "John Doe\nPython developer"
        hash1 = hash_profile_text(text)
        hash2 = hash_profile_text(text)
        assert hash1 == hash2

    def test_hash_is_unique_for_different_text(self) -> None:
        """Test different text produces different hash."""
        hash1 = hash_profile_text("Profile 1")
        hash2 = hash_profile_text("Profile 2")
        assert hash1 != hash2

    def test_hash_has_expected_length(self) -> None:
        """Test hash has consistent length."""
        hash_val = hash_profile_text("Test profile")
        assert len(hash_val) == 16  # First 16 chars of SHA256
