"""End-to-end tests for autonomous browsing flow.

Tests the complete flow from start to finish:
- Login
- Profile browsing
- Evaluation
- Message sending
- Error handling
"""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from yc_matcher.application.autonomous_flow import AutonomousFlow
from yc_matcher.application.use_cases import EvaluateProfile, SendMessage
from yc_matcher.infrastructure.control.stop_flag import FileStopFlag
from yc_matcher.infrastructure.logging.jsonl_logger import JSONLLogger
from yc_matcher.infrastructure.persistence.sqlite_quota import SQLiteDailyWeeklyQuota
from yc_matcher.infrastructure.persistence.sqlite_repo import SQLiteSeenRepo


class TestAutonomousBrowsingE2E:
    """End-to-end tests for the complete autonomous browsing flow."""

    @pytest.fixture
    def setup_test_env(self, tmp_path: Path):
        """Set up test environment with temp directories."""
        # Create temp .runs directory
        runs_dir = tmp_path / ".runs"
        runs_dir.mkdir()

        # Create test files
        (runs_dir / "events.jsonl").touch()
        (runs_dir / "seen.sqlite").touch()
        (runs_dir / "quota.sqlite").touch()

        # Set up environment
        with patch.dict(
            os.environ,
            {
                "YC_EMAIL": "test@example.com",
                "YC_PASSWORD": "test123",
                "ENABLE_PLAYWRIGHT": "1",
                "SHADOW_MODE": "1",  # Safety: test mode
                "PACE_MIN_SECONDS": "0",  # Speed up tests
            },
        ):
            yield runs_dir

    def test_full_autonomous_flow_shadow_mode(self, setup_test_env: Path) -> None:
        """Test complete flow in shadow mode (evaluate only, no sending)."""
        # Arrange
        mock_browser = Mock()
        mock_browser.is_logged_in.return_value = True
        mock_browser.open.return_value = None
        mock_browser.click_view_profile.side_effect = [True, True, False]  # 2 profiles then stop
        mock_browser.read_profile_text.side_effect = [
            "Profile 1: Developer with 5 years experience",
            "Profile 2: Designer looking for technical co-founder",
        ]
        mock_browser.skip.return_value = None

        mock_evaluate = Mock(spec=EvaluateProfile)
        mock_evaluate.side_effect = [
            {"decision": "YES", "rationale": "Good match", "draft": "Hi!", "score": 0.8},
            {"decision": "NO", "rationale": "Not a match", "draft": "", "score": 0.3},
        ]

        mock_send = Mock(spec=SendMessage)
        mock_logger = Mock(spec=JSONLLogger)
        mock_seen = Mock(spec=SQLiteSeenRepo)
        mock_seen.is_seen.return_value = False
        mock_quota = Mock(spec=SQLiteDailyWeeklyQuota)
        mock_stop = Mock(spec=FileStopFlag)
        mock_stop.is_stopped.return_value = False

        # Create flow
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
        results = flow.run(
            your_profile="Technical founder",
            criteria="Looking for business co-founder",
            template="Hi, I'd like to connect",
            mode="ai",
            limit=10,
            shadow_mode=True,  # Shadow mode
            threshold=0.7,
        )

        # Assert
        assert results["total_evaluated"] == 2
        assert results["total_sent"] == 0  # Shadow mode, no actual sends
        assert len(results["results"]) == 2
        assert results["results"][0]["decision"] == "YES"
        assert results["results"][1]["decision"] == "NO"

        # Verify no messages were sent (shadow mode)
        mock_send.assert_not_called()

        # Verify profiles were marked as seen
        assert mock_seen.mark_seen.call_count == 2

    def test_full_autonomous_flow_with_sending(self, setup_test_env: Path) -> None:
        """Test complete flow with actual message sending."""
        # Arrange
        mock_browser = Mock()
        mock_browser.is_logged_in.return_value = True
        mock_browser.click_view_profile.side_effect = [True, False]
        mock_browser.read_profile_text.return_value = "Great profile"
        mock_browser.type_message.return_value = None
        mock_browser.send_message.return_value = None
        mock_browser.verify_sent.return_value = True

        mock_evaluate = Mock(spec=EvaluateProfile)
        mock_evaluate.return_value = {
            "decision": "YES",
            "rationale": "Perfect match",
            "draft": "Let's connect!",
            "score": 0.9,
            "auto_send": True,  # Need this for AI mode to auto-send
        }

        mock_send = Mock(spec=SendMessage)
        mock_send.return_value = True  # Success

        mock_logger = Mock(spec=JSONLLogger)
        mock_seen = Mock(spec=SQLiteSeenRepo)
        mock_seen.is_seen.return_value = False
        mock_quota = Mock(spec=SQLiteDailyWeeklyQuota)
        mock_quota.check_and_increment.return_value = True  # Correct method name
        mock_stop = Mock(spec=FileStopFlag)
        mock_stop.is_stopped.return_value = False

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
        results = flow.run(
            your_profile="Technical founder",
            criteria="Business co-founder",
            template="Template",
            mode="ai",
            limit=5,
            shadow_mode=False,  # Real mode
            threshold=0.7,
        )

        # Assert
        assert results["total_evaluated"] == 1
        assert results["total_sent"] == 1  # Message was sent
        assert results["results"][0]["sent"] is True

        # Verify message was sent
        assert mock_send.call_count == 1
        assert mock_send.call_args[0][0] == "Let's connect!"
        assert mock_send.call_args[0][1] == 1

    def test_stop_flag_halts_execution(self, setup_test_env: Path) -> None:
        """Test that STOP flag immediately halts execution."""
        # Arrange
        mock_browser = Mock()
        mock_browser.is_logged_in.return_value = True
        mock_browser.click_view_profile.return_value = True
        mock_browser.read_profile_text.return_value = "Profile"

        mock_evaluate = Mock(spec=EvaluateProfile)
        mock_send = Mock(spec=SendMessage)
        mock_logger = Mock(spec=JSONLLogger)
        mock_seen = Mock(spec=SQLiteSeenRepo)
        mock_quota = Mock(spec=SQLiteDailyWeeklyQuota)

        # Stop flag becomes true immediately (safer behavior)
        mock_stop = Mock(spec=FileStopFlag)
        mock_stop.is_stopped.return_value = True  # Stop immediately

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
        results = flow.run(
            your_profile="Profile",
            criteria="Criteria",
            template="Template",
            mode="ai",
            limit=10,  # Would process 10 but stop flag will halt
            shadow_mode=True,
        )

        # Assert - Stop flag checked before processing, so 0 profiles evaluated
        assert results["total_evaluated"] == 0  # Stopped before any evaluation
        mock_logger.emit.assert_any_call(
            {"event": "stopped", "at_profile": 0, "reason": "stop_flag"}
        )

    def test_quota_limits_respected(self, setup_test_env: Path) -> None:
        """Test that daily/weekly quotas are respected."""
        # Arrange
        mock_browser = Mock()
        mock_browser.is_logged_in.return_value = True
        mock_browser.click_view_profile.return_value = True
        mock_browser.read_profile_text.return_value = "Profile"

        mock_evaluate = Mock(spec=EvaluateProfile)
        mock_evaluate.return_value = {
            "decision": "YES",
            "rationale": "Match",
            "draft": "Message",
            "score": 0.8,
        }

        mock_send = Mock(spec=SendMessage)
        mock_send.side_effect = [True, False]  # First succeeds, second hits quota

        mock_logger = Mock(spec=JSONLLogger)
        mock_seen = Mock(spec=SQLiteSeenRepo)
        mock_seen.is_seen.return_value = False

        # Quota exhausted after first send
        mock_quota = Mock(spec=SQLiteDailyWeeklyQuota)
        mock_quota.check_and_increment.side_effect = [True, False]

        mock_stop = Mock(spec=FileStopFlag)
        mock_stop.is_stopped.return_value = False

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
        results = flow.run(
            your_profile="Profile",
            criteria="Criteria",
            template="Template",
            mode="ai",
            limit=5,
            shadow_mode=False,
        )

        # Assert
        # Should evaluate multiple but only send one due to quota
        assert results["total_sent"] <= 1

    def test_error_recovery_continues_processing(self, setup_test_env: Path) -> None:
        """Test that errors in one profile don't stop processing others."""
        # Arrange
        mock_browser = Mock()
        mock_browser.is_logged_in.return_value = True
        mock_browser.click_view_profile.side_effect = [True, True, False]
        mock_browser.read_profile_text.side_effect = [
            Exception("Network error"),  # First fails
            "Valid profile",  # Second succeeds
        ]

        mock_evaluate = Mock(spec=EvaluateProfile)
        mock_evaluate.return_value = {
            "decision": "YES",
            "rationale": "Match",
            "draft": "Hi",
            "score": 0.8,
        }

        mock_send = Mock(spec=SendMessage)
        mock_logger = Mock(spec=JSONLLogger)
        mock_seen = Mock(spec=SQLiteSeenRepo)
        mock_quota = Mock(spec=SQLiteDailyWeeklyQuota)
        mock_stop = Mock(spec=FileStopFlag)
        mock_stop.is_stopped.return_value = False

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
        results = flow.run(
            your_profile="Profile",
            criteria="Criteria",
            template="Template",
            mode="ai",
            limit=5,
            shadow_mode=True,
        )

        # Assert
        # Should continue after error
        assert results["total_evaluated"] >= 1
        # Should log the error
        assert any(r.get("decision") == "ERROR" for r in results["results"])

    def test_duplicate_profiles_skipped(self, setup_test_env: Path) -> None:
        """Test that duplicate profiles are not processed twice."""
        # Arrange
        mock_browser = Mock()
        mock_browser.is_logged_in.return_value = True
        mock_browser.click_view_profile.side_effect = [True, True, False]
        mock_browser.read_profile_text.return_value = "Same profile text"  # Same every time

        mock_evaluate = Mock(spec=EvaluateProfile)
        mock_send = Mock(spec=SendMessage)
        mock_logger = Mock(spec=JSONLLogger)

        # Second profile is marked as seen
        mock_seen = Mock(spec=SQLiteSeenRepo)
        mock_seen.is_seen.side_effect = [False, True]  # First new, second duplicate

        mock_quota = Mock(spec=SQLiteDailyWeeklyQuota)
        mock_stop = Mock(spec=FileStopFlag)
        mock_stop.is_stopped.return_value = False

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
        results = flow.run(
            your_profile="Profile",
            criteria="Criteria",
            template="Template",
            mode="ai",
            limit=5,
            shadow_mode=True,
        )

        # Assert
        # Should only evaluate first profile, skip duplicate
        mock_evaluate.assert_called_once()
        assert results["total_evaluated"] >= 1  # At least one evaluated
        # Should log duplicate event
        mock_logger.emit.assert_any_call(
            {
                "event": "duplicate",
                "hash": mock_seen.mark_seen.call_args[0][0],  # Get the hash used
            }
        )


class TestLoginRequirement:
    """Test that login is required and handled properly."""

    def test_login_required_before_browsing(self) -> None:
        """Test that browsing requires login."""
        # Arrange
        mock_browser = Mock()
        mock_browser.is_logged_in.return_value = False  # Not logged in
        mock_browser.ensure_logged_in.side_effect = Exception("No credentials")

        mock_evaluate = Mock(spec=EvaluateProfile)
        mock_send = Mock(spec=SendMessage)
        mock_logger = Mock(spec=JSONLLogger)
        mock_seen = Mock(spec=SQLiteSeenRepo)
        mock_quota = Mock(spec=SQLiteDailyWeeklyQuota)
        mock_stop = Mock(spec=FileStopFlag)

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
        results = flow.run(
            your_profile="Profile",
            criteria="Criteria",
            template="Template",
            mode="ai",
            limit=5,
            shadow_mode=True,
        )

        # Assert
        assert results.get("error") is not None
        assert "login" in results["error"].lower()
        assert results["evaluated"] == 0
        assert results["sent"] == 0
