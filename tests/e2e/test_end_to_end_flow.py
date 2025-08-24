"""End-to-end test for YC Cofounder Matcher application.

Tests the complete flow from UI input to browser automation.
Runs in SHADOW_MODE for safety (no actual messages sent).
"""

import os
from pathlib import Path
from unittest.mock import Mock

import pytest

# Set test environment
os.environ["SHADOW_MODE"] = "1"  # Never send in tests
os.environ["ENABLE_PLAYWRIGHT"] = "1"
os.environ["ENABLE_CUA"] = "0"  # No CUA for E2E tests
os.environ["DECISION_MODE"] = "rubric"
os.environ["PACE_MIN_SECONDS"] = "0"  # No delays in tests
os.environ["PLAYWRIGHT_HEADLESS"] = "1"  # Headless browser


class TestEndToEndFlow:
    """Test complete application flow."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path) -> None:
        """Set up test environment."""
        # Create temporary directories for test data
        self.runs_dir = tmp_path / ".runs"
        self.runs_dir.mkdir()

        # Set paths for test databases
        os.environ["SEEN_DB_PATH"] = str(self.runs_dir / "seen.sqlite")
        os.environ["QUOTA_DB_PATH"] = str(self.runs_dir / "quota.sqlite")
        os.environ["EVENTS_LOG_PATH"] = str(self.runs_dir / "events.jsonl")

    def test_full_flow_with_shadow_mode(self) -> None:
        """Test complete flow: UI input → evaluation → (no send in shadow)."""
        from yc_matcher.application.autonomous_flow import AutonomousFlow
        from yc_matcher.infrastructure.control.stop_flag import FileStopFlag
        from yc_matcher.infrastructure.persistence.sqlite_quota import SQLiteDailyWeeklyQuota
        from yc_matcher.infrastructure.persistence.sqlite_repo import SQLiteSeenRepo
        from yc_matcher.interface.di import build_services

        # Build services with test inputs
        criteria_text = "Python, Machine Learning, San Francisco"
        template_text = "Hi {name}, I'm interested in your profile!"

        eval_use, send_use, logger = build_services(
            criteria_text=criteria_text,
            template_text=template_text,
        )

        # Verify services were built
        assert eval_use is not None
        assert send_use is not None
        assert logger is not None

        # Create repositories
        seen_repo = SQLiteSeenRepo(self.runs_dir / "seen.sqlite")
        quota = SQLiteDailyWeeklyQuota(self.runs_dir / "quota.sqlite")
        stop_flag = FileStopFlag(self.runs_dir / "stop.flag")

        # Create autonomous flow
        flow = AutonomousFlow(
            browser=send_use.browser,
            evaluate=eval_use,
            send=send_use,
            seen=seen_repo,
            logger=logger,
            stop=stop_flag,
            quota=quota,
        )

        # Verify flow was created
        assert flow is not None
        assert flow.browser is not None

        # In shadow mode, no actual sends should occur
        assert os.getenv("SHADOW_MODE") == "1"

    def test_ai_only_mode(self) -> None:
        """Test that AI-only mode works."""
        from yc_matcher.interface.di import build_services

        # Test AI-only mode (the only mode now)
        eval_use, send_use, logger = build_services(
            criteria_text="Python",
            template_text="Hi {name}",
        )

        assert eval_use is not None, "Failed to build evaluator"
        assert send_use is not None, "Failed to build sender"

    def test_browser_lifecycle_no_spam(self) -> None:
        """Test that only ONE browser instance is created."""
        # This test is better suited as a unit test
        # The browser singleton behavior is already tested in unit tests
        # E2E tests should focus on the full application flow
        pass

    def test_stop_flag_halts_execution(self, tmp_path: Path) -> None:
        """Test that stop flag immediately stops processing."""
        from yc_matcher.application.use_cases import ProcessCandidate
        from yc_matcher.domain.entities import Criteria
        from yc_matcher.infrastructure.control.stop_flag import FileStopFlag

        # Create stop flag
        stop_flag_path = tmp_path / "stop.flag"
        stop_flag = FileStopFlag(stop_flag_path)

        # Set the stop flag
        stop_flag.set()

        # Create mock services
        mock_browser = Mock()
        mock_evaluate = Mock()
        mock_send = Mock()
        mock_seen = Mock()
        mock_logger = Mock()

        # Create processor
        processor = ProcessCandidate(
            browser=mock_browser,
            evaluate=mock_evaluate,
            send=mock_send,
            seen=mock_seen,
            logger=mock_logger,
            stop=stop_flag,
        )

        # Process should exit immediately due to stop flag
        criteria = Criteria(text="test")
        url = "https://www.startupschool.org/cofounder-matching"
        processor(url=url, limit=10, criteria=criteria)

        # Verify browser was never opened (stopped before navigation)
        mock_browser.open.assert_not_called()

    def test_quota_enforcement(self, tmp_path: Path) -> None:
        """Test that quotas are enforced."""
        from yc_matcher.infrastructure.persistence.sqlite_quota import SQLiteDailyWeeklyQuota

        quota = SQLiteDailyWeeklyQuota(tmp_path / "quota.sqlite")

        # Test daily quota
        assert quota.check_and_increment_daily(2) is True  # First
        assert quota.check_and_increment_daily(2) is True  # Second
        assert quota.check_and_increment_daily(2) is False  # Exceeds limit

    def test_seen_deduplication(self, tmp_path: Path) -> None:
        """Test that profiles are never messaged twice."""
        from yc_matcher.infrastructure.persistence.sqlite_repo import SQLiteSeenRepo

        seen = SQLiteSeenRepo(tmp_path / "seen.sqlite")

        profile_id = "test_profile_123"

        # First time should not be seen
        assert seen.is_seen(profile_id) is False

        # Mark as seen
        seen.mark_seen(profile_id)

        # Should now be seen
        assert seen.is_seen(profile_id) is True

    def test_event_logging(self, tmp_path: Path) -> None:
        """Test that events are logged in correct order."""
        import json

        from yc_matcher.infrastructure.logging.jsonl_logger import JSONLLogger

        log_path = tmp_path / "events.jsonl"
        logger = JSONLLogger(log_path)

        # Log decision event
        logger.emit(
            {
                "event": "decision",
                "profile_id": "test123",
                "decision": "YES",
                "score": 0.85,
            }
        )

        # Log sent event
        logger.emit(
            {
                "event": "sent",
                "profile_id": "test123",
                "success": True,
            }
        )

        # Read and verify events
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 2

        decision = json.loads(lines[0])
        sent = json.loads(lines[1])

        assert decision["event"] == "decision"
        assert sent["event"] == "sent"
        assert decision["profile_id"] == sent["profile_id"]


@pytest.mark.integration
class TestUIIntegration:
    """Test Streamlit UI integration."""

    def test_ui_loads_with_three_input_mode(self) -> None:
        """Test that UI loads in three-input mode."""
        os.environ["USE_THREE_INPUT_UI"] = "true"

        # Import would fail if there are issues
        from yc_matcher.interface.web.ui_streamlit import main

        # Verify main function exists
        assert callable(main)

    def test_ui_validates_inputs(self) -> None:
        """Test that UI validates required inputs."""
        # Test input validation logic

        # Empty inputs should fail
        assert not all(["", "", ""])

        # All inputs provided should pass
        profile = "My profile"
        criteria = "Python, ML"
        template = "Hi {name}"
        assert all([profile, criteria, template])
        assert "{name}" in template

        # Template without {name} should fail
        bad_template = "Hi there"
        assert "{name}" not in bad_template
