"""Unit tests for use cases."""

import os
from unittest.mock import Mock, patch

from yc_matcher.application.use_cases import EvaluateProfile, ProcessCandidate, SendMessage
from yc_matcher.domain.entities import Criteria, Profile


class TestEvaluateProfile:
    """Test EvaluateProfile use case."""

    def test_evaluate_profile_returns_decision_with_draft(self) -> None:
        """Test that EvaluateProfile returns decision data with draft."""
        # Arrange
        mock_decision = Mock()
        mock_decision.evaluate.return_value = {
            "decision": "YES",
            "score": 0.85,
            "confidence": 0.9,
            "rationale": "Good match",
        }

        mock_message = Mock()
        mock_message.render.return_value = "Hi! I'd love to connect..."

        use_case = EvaluateProfile(decision=mock_decision, message=mock_message)
        profile = Profile(raw_text="Test profile")
        criteria = Criteria(text="Test criteria")

        # Act
        result = use_case(profile, criteria)

        # Assert
        assert result["decision"] == "YES"
        assert result["score"] == 0.85
        assert result["confidence"] == 0.9
        assert result["draft"] == "Hi! I'd love to connect..."
        mock_decision.evaluate.assert_called_once_with(profile, criteria)
        mock_message.render.assert_called_once()


class TestSendMessage:
    """Test SendMessage use case."""

    def test_send_message_success_flow(self) -> None:
        """Test successful message sending flow."""
        # Arrange
        mock_quota = Mock()
        mock_quota.check_and_increment.return_value = True

        mock_browser = Mock()
        mock_browser.verify_sent.return_value = True

        mock_logger = Mock()
        mock_stop = Mock()
        mock_stop.is_stopped.return_value = False

        use_case = SendMessage(
            quota=mock_quota,
            browser=mock_browser,
            logger=mock_logger,
            stop=mock_stop,
        )

        # Act
        with patch.dict(os.environ, {"PACE_MIN_SECONDS": "0", "PACE_BLOCKING": "0"}):
            result = use_case(draft="Test message", limit=25)

        # Assert
        assert result is True
        mock_quota.check_and_increment.assert_called_once_with(25)
        mock_browser.focus_message_box.assert_called_once()
        mock_browser.fill_message.assert_called_once_with("Test message")
        mock_browser.send.assert_called_once()
        mock_browser.verify_sent.assert_called_once()

        # Check logging
        calls = [call[0][0] for call in mock_logger.emit.call_args_list]
        assert any(c.get("event") == "send_gate" for c in calls)
        assert any(c.get("event") == "sent" and c.get("ok") is True for c in calls)

    def test_send_message_blocked_by_stop_flag(self) -> None:
        """Test that stop flag prevents sending."""
        # Arrange
        mock_quota = Mock()
        mock_browser = Mock()
        mock_logger = Mock()
        mock_stop = Mock()
        mock_stop.is_stopped.return_value = True  # Stop is set

        use_case = SendMessage(
            quota=mock_quota,
            browser=mock_browser,
            logger=mock_logger,
            stop=mock_stop,
        )

        # Act
        result = use_case(draft="Test message", limit=25)

        # Assert
        assert result is False
        mock_quota.check_and_increment.assert_not_called()
        mock_browser.send.assert_not_called()

        # Check logging
        calls = [call[0][0] for call in mock_logger.emit.call_args_list]
        assert any(c.get("event") == "stopped" for c in calls)

    def test_send_message_blocked_by_quota(self) -> None:
        """Test that quota limit prevents sending."""
        # Arrange
        mock_quota = Mock()
        mock_quota.check_and_increment.return_value = False  # Quota exceeded

        mock_browser = Mock()
        mock_logger = Mock()
        mock_stop = Mock()
        mock_stop.is_stopped.return_value = False

        use_case = SendMessage(
            quota=mock_quota,
            browser=mock_browser,
            logger=mock_logger,
            stop=mock_stop,
        )

        # Act
        result = use_case(draft="Test message", limit=25)

        # Assert
        assert result is False
        mock_browser.send.assert_not_called()

        # Check logging
        calls = [call[0][0] for call in mock_logger.emit.call_args_list]
        assert any(c.get("event") == "quota_block" for c in calls)

    def test_send_message_retry_on_verify_failure(self) -> None:
        """Test that send retries once if verification fails."""
        # Arrange
        mock_quota = Mock()
        mock_quota.check_and_increment.return_value = True

        mock_browser = Mock()
        # First verify fails, second succeeds
        mock_browser.verify_sent.side_effect = [False, True]

        mock_logger = Mock()
        mock_stop = Mock()
        mock_stop.is_stopped.return_value = False

        use_case = SendMessage(
            quota=mock_quota,
            browser=mock_browser,
            logger=mock_logger,
            stop=mock_stop,
        )

        # Act
        with patch.dict(os.environ, {"PACE_MIN_SECONDS": "0", "PACE_BLOCKING": "0"}):
            result = use_case(draft="Test message", limit=25)

        # Assert
        assert result is True
        assert mock_browser.send.call_count == 2  # Called twice due to retry
        assert mock_browser.verify_sent.call_count == 2

        # Check logging
        calls = [call[0][0] for call in mock_logger.emit.call_args_list]
        assert any(c.get("event") == "verify_failed" for c in calls)
        assert any(c.get("event") == "sent" and c.get("retry") == 1 for c in calls)

    def test_send_message_stop_check_between_steps(self) -> None:
        """Test that stop flag is checked between each step."""
        # Arrange
        mock_quota = Mock()
        mock_quota.check_and_increment.return_value = True

        mock_browser = Mock()
        mock_logger = Mock()
        mock_stop = Mock()

        # Stop flag becomes true after focus_message_box
        def stop_after_focus(*args):
            if mock_browser.focus_message_box.called:
                return True
            return False

        mock_stop.is_stopped.side_effect = stop_after_focus

        use_case = SendMessage(
            quota=mock_quota,
            browser=mock_browser,
            logger=mock_logger,
            stop=mock_stop,
        )

        # Act
        result = use_case(draft="Test message", limit=25)

        # Assert
        assert result is False
        mock_browser.focus_message_box.assert_called_once()
        mock_browser.fill_message.assert_not_called()  # Should not proceed
        mock_browser.send.assert_not_called()


class TestProcessCandidate:
    """Test ProcessCandidate use case."""

    def test_process_candidate_full_flow(self) -> None:
        """Test processing a candidate from URL to decision."""
        # Arrange
        mock_evaluate = Mock()
        mock_evaluate.return_value = {
            "decision": "YES",
            "score": 0.85,
            "draft": "Hi there!",
        }

        mock_send = Mock()
        mock_send.return_value = True

        mock_browser = Mock()
        mock_browser.click_view_profile.return_value = True
        mock_browser.read_profile_text.return_value = "Profile text"

        mock_seen = Mock()
        mock_seen.is_seen.return_value = False

        mock_logger = Mock()
        mock_progress = Mock()
        mock_stop = Mock()
        mock_stop.is_stopped.return_value = False

        use_case = ProcessCandidate(
            evaluate=mock_evaluate,
            send=mock_send,
            browser=mock_browser,
            seen=mock_seen,
            logger=mock_logger,
            progress=mock_progress,
            stop=mock_stop,
        )

        criteria = Criteria(text="Test criteria")

        # Act
        use_case(
            url="https://test.com/profile",
            criteria=criteria,
            limit=25,
            auto_send=True,
        )

        # Assert
        mock_browser.open.assert_called_once_with("https://test.com/profile")
        mock_browser.click_view_profile.assert_called_once()
        mock_browser.read_profile_text.assert_called_once()
        mock_seen.is_seen.assert_called_once()
        mock_seen.mark_seen.assert_called_once()
        mock_evaluate.assert_called_once()
        mock_send.assert_called_once_with("Hi there!", 25)
        mock_progress.set_last.assert_called_once()

        # Check logging
        calls = [call[0][0] for call in mock_logger.emit.call_args_list]
        assert any(c.get("event") == "decision" for c in calls)
        assert any(c.get("event") == "auto_send" for c in calls)

    def test_process_candidate_skip_seen_profile(self) -> None:
        """Test that seen profiles are skipped."""
        # Arrange
        mock_evaluate = Mock()
        mock_send = Mock()

        mock_browser = Mock()
        mock_browser.click_view_profile.return_value = True
        mock_browser.read_profile_text.return_value = "Profile text"

        mock_seen = Mock()
        mock_seen.is_seen.return_value = True  # Already seen

        mock_logger = Mock()

        use_case = ProcessCandidate(
            evaluate=mock_evaluate,
            send=mock_send,
            browser=mock_browser,
            seen=mock_seen,
            logger=mock_logger,
        )

        criteria = Criteria(text="Test criteria")

        # Act
        use_case(
            url="https://test.com/profile",
            criteria=criteria,
            limit=25,
            auto_send=True,
        )

        # Assert
        mock_browser.skip.assert_called_once()
        mock_evaluate.assert_not_called()
        mock_send.assert_not_called()

        # Check logging
        calls = [call[0][0] for call in mock_logger.emit.call_args_list]
        assert any(c.get("event") == "skip_seen" for c in calls)

    def test_process_candidate_no_profile_button(self) -> None:
        """Test handling when no profile button is found."""
        # Arrange
        mock_evaluate = Mock()
        mock_send = Mock()

        mock_browser = Mock()
        mock_browser.click_view_profile.return_value = False  # No button

        mock_seen = Mock()
        mock_logger = Mock()

        use_case = ProcessCandidate(
            evaluate=mock_evaluate,
            send=mock_send,
            browser=mock_browser,
            seen=mock_seen,
            logger=mock_logger,
        )

        criteria = Criteria(text="Test criteria")

        # Act
        use_case(
            url="https://test.com/profile",
            criteria=criteria,
            limit=25,
            auto_send=True,
        )

        # Assert
        mock_browser.read_profile_text.assert_not_called()
        mock_evaluate.assert_not_called()
        mock_send.assert_not_called()

        # Check logging
        calls = [call[0][0] for call in mock_logger.emit.call_args_list]
        assert any(c.get("event") == "no_profile" for c in calls)

    def test_process_candidate_stop_flag_early_exit(self) -> None:
        """Test that stop flag causes early exit."""
        # Arrange
        mock_evaluate = Mock()
        mock_send = Mock()
        mock_browser = Mock()
        mock_seen = Mock()
        mock_logger = Mock()
        mock_stop = Mock()
        mock_stop.is_stopped.return_value = True  # Stop is set

        use_case = ProcessCandidate(
            evaluate=mock_evaluate,
            send=mock_send,
            browser=mock_browser,
            seen=mock_seen,
            logger=mock_logger,
            stop=mock_stop,
        )

        criteria = Criteria(text="Test criteria")

        # Act
        use_case(
            url="https://test.com/profile",
            criteria=criteria,
            limit=25,
            auto_send=True,
        )

        # Assert
        mock_browser.open.assert_not_called()
        mock_evaluate.assert_not_called()
        mock_send.assert_not_called()

        # Check logging
        calls = [call[0][0] for call in mock_logger.emit.call_args_list]
        assert any(c.get("event") == "stopped" for c in calls)
