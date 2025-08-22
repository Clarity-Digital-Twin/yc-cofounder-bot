"""Test login preflight gate in AutonomousFlow.

Following TDD: Test that login is properly checked before processing.
"""

from unittest.mock import MagicMock, patch

from yc_matcher.application.autonomous_flow import AutonomousFlow
from yc_matcher.application.use_cases import EvaluateProfile, SendMessage


class TestLoginPreflight:
    """Test that login gate blocks unauthorized access."""

    def test_login_preflight_blocks_when_not_logged_in(self) -> None:
        """Test that flow returns error when not logged in and no credentials."""
        # Arrange
        mock_browser = MagicMock()
        mock_browser.is_logged_in.return_value = False
        mock_browser.open = MagicMock()

        mock_evaluate = MagicMock(spec=EvaluateProfile)
        mock_send = MagicMock(spec=SendMessage)
        mock_seen = MagicMock()
        mock_logger = MagicMock()
        mock_stop = MagicMock()
        mock_stop.is_stopped.return_value = False
        mock_quota = MagicMock()

        flow = AutonomousFlow(
            browser=mock_browser,
            evaluate=mock_evaluate,
            send=mock_send,
            seen=mock_seen,
            logger=mock_logger,
            stop=mock_stop,
            quota=mock_quota,
        )

        # Remove credentials
        with patch.dict("os.environ", {"YC_EMAIL": "", "YC_PASSWORD": ""}, clear=False):
            # Act
            result = flow.run(
                your_profile="Test profile",
                criteria="Test criteria",
                template="Test template",
                limit=5,
            )

        # Assert
        assert "error" in result
        assert "Manual login required" in result["error"]
        assert result.get("evaluated") == 0
        assert result.get("sent") == 0

        # Should not have navigated
        mock_browser.open.assert_not_called()

        # Should have logged the event
        mock_logger.emit.assert_any_call({"event": "login_required", "has_credentials": False})

    def test_login_preflight_auto_login_with_credentials(self) -> None:
        """Test that flow attempts auto-login when credentials are available."""
        # Arrange
        mock_browser = MagicMock()
        mock_browser.is_logged_in.side_effect = [
            False,
            True,
        ]  # Not logged in, then logged in after ensure_logged_in
        mock_browser.ensure_logged_in = MagicMock()
        mock_browser.click_view_profile.return_value = False  # No profiles to process

        mock_evaluate = MagicMock(spec=EvaluateProfile)
        mock_send = MagicMock(spec=SendMessage)
        mock_seen = MagicMock()
        mock_logger = MagicMock()
        mock_stop = MagicMock()
        mock_stop.is_stopped.return_value = False
        mock_quota = MagicMock()

        flow = AutonomousFlow(
            browser=mock_browser,
            evaluate=mock_evaluate,
            send=mock_send,
            seen=mock_seen,
            logger=mock_logger,
            stop=mock_stop,
            quota=mock_quota,
        )

        # Set credentials
        with patch.dict(
            "os.environ", {"YC_EMAIL": "test@example.com", "YC_PASSWORD": "password123"}
        ):
            # Act
            result = flow.run(
                your_profile="Test profile",
                criteria="Test criteria",
                template="Test template",
                limit=5,
            )

        # Assert - should succeed
        assert "error" not in result or result["error"] is None

        # Should have attempted auto-login
        mock_browser.ensure_logged_in.assert_called_once()

        # Should have logged success
        mock_logger.emit.assert_any_call({"event": "auto_login_attempt"})
        mock_logger.emit.assert_any_call({"event": "auto_login_success"})

    def test_login_preflight_auto_login_failure(self) -> None:
        """Test that flow returns error when auto-login fails."""
        # Arrange
        mock_browser = MagicMock()
        mock_browser.is_logged_in.return_value = False
        mock_browser.ensure_logged_in.side_effect = Exception("Login failed")

        mock_evaluate = MagicMock(spec=EvaluateProfile)
        mock_send = MagicMock(spec=SendMessage)
        mock_seen = MagicMock()
        mock_logger = MagicMock()
        mock_stop = MagicMock()
        mock_stop.is_stopped.return_value = False
        mock_quota = MagicMock()

        flow = AutonomousFlow(
            browser=mock_browser,
            evaluate=mock_evaluate,
            send=mock_send,
            seen=mock_seen,
            logger=mock_logger,
            stop=mock_stop,
            quota=mock_quota,
        )

        # Set credentials
        with patch.dict("os.environ", {"YC_EMAIL": "test@example.com", "YC_PASSWORD": "wrong"}):
            # Act
            result = flow.run(
                your_profile="Test profile",
                criteria="Test criteria",
                template="Test template",
                limit=5,
            )

        # Assert
        assert "error" in result
        assert "Auto-login failed" in result["error"]
        assert result.get("evaluated") == 0
        assert result.get("sent") == 0

        # Should have logged failure
        mock_logger.emit.assert_any_call({"event": "auto_login_failed", "error": "Login failed"})

    def test_login_check_after_navigation(self) -> None:
        """Test that login is verified after navigating to YC page."""
        # Arrange
        mock_browser = MagicMock()
        # Logged in initially, but lost after navigation
        mock_browser.is_logged_in.side_effect = [True, False]

        mock_evaluate = MagicMock(spec=EvaluateProfile)
        mock_send = MagicMock(spec=SendMessage)
        mock_seen = MagicMock()
        mock_logger = MagicMock()
        mock_stop = MagicMock()
        mock_stop.is_stopped.return_value = False
        mock_quota = MagicMock()

        flow = AutonomousFlow(
            browser=mock_browser,
            evaluate=mock_evaluate,
            send=mock_send,
            seen=mock_seen,
            logger=mock_logger,
            stop=mock_stop,
            quota=mock_quota,
        )

        # Act
        result = flow.run(
            your_profile="Test profile",
            criteria="Test criteria",
            template="Test template",
            limit=5,
        )

        # Assert
        assert "error" in result
        assert "Login required after navigation" in result["error"]
        assert result.get("evaluated") == 0

        # Should have navigated
        mock_browser.open.assert_called_once()

        # Should have logged the event
        mock_logger.emit.assert_any_call({"event": "login_lost_after_navigation"})
