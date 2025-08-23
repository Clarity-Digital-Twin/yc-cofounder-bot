"""Test duplicate profile detection."""

from unittest.mock import Mock, call

from yc_matcher.application.autonomous_flow import AutonomousFlow, hash_profile_text


class TestDuplicateDetection:
    """Test that duplicate profiles are properly detected and skipped."""

    def test_duplicate_profile_skipped(self) -> None:
        """Same profile text should be skipped on second encounter."""
        # Arrange
        browser = Mock()
        browser.open = Mock()
        browser.click_view_profile = Mock(return_value=True)
        # Return same profile text twice
        browser.read_profile_text = Mock(side_effect=["Duplicate profile", "Duplicate profile", "Unique profile"])
        browser.skip = Mock()

        evaluate = Mock(return_value={"decision": "NO", "rationale": "No match"})
        send = Mock()

        # Mock seen repo to detect duplicate on second occurrence
        seen = Mock()
        seen.is_seen = Mock(side_effect=[False, True, False])  # Second is duplicate
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
            limit=3,
            shadow_mode=False,
        )

        # Assert
        assert results["total_evaluated"] == 2  # Only unique profiles evaluated
        assert results["total_skipped"] == 1  # One duplicate skipped

        # Should evaluate only the unique profiles
        assert evaluate.call_count == 2

        # Should mark seen for unique profiles
        expected_calls = [
            call(hash_profile_text("Duplicate profile")),
            call(hash_profile_text("Unique profile")),
        ]
        seen.mark_seen.assert_has_calls(expected_calls, any_order=False)

        # Should log duplicate event
        duplicate_hash = hash_profile_text("Duplicate profile")
        logger.emit.assert_any_call({"event": "duplicate", "hash": duplicate_hash})

        # Should skip the duplicate
        assert browser.skip.call_count >= 1

    def test_hash_function_is_deterministic(self) -> None:
        """Hash function should produce same hash for same text."""
        text = "John Doe\nPython developer with 5 years experience"

        hash1 = hash_profile_text(text)
        hash2 = hash_profile_text(text)

        assert hash1 == hash2
        assert len(hash1) == 16  # First 16 chars of SHA256

    def test_hash_function_differs_for_different_text(self) -> None:
        """Different profiles should have different hashes."""
        hash1 = hash_profile_text("Profile A")
        hash2 = hash_profile_text("Profile B")

        assert hash1 != hash2
