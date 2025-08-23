"""Test STOP flag integration with autonomous flow."""

from unittest.mock import Mock
from yc_matcher.application.autonomous_flow import AutonomousFlow


class TestStopFlagIntegration:
    """Test that STOP flag halts execution immediately."""

    def test_stop_flag_before_run_prevents_all_processing(self) -> None:
        """If STOP flag exists at start, should not process any profiles."""
        # Arrange
        browser = Mock()
        browser.open = Mock()
        browser.click_view_profile = Mock(return_value=True)
        browser.read_profile_text = Mock(return_value="Profile text")
        
        evaluate = Mock(return_value={"decision": "YES", "draft": "Hi!", "auto_send": True})
        send = Mock(return_value=True)
        seen = Mock()
        seen.is_seen = Mock(return_value=False)
        
        logger = Mock()
        
        # STOP flag is set from the beginning
        stop = Mock()
        stop.is_stopped = Mock(return_value=True)
        
        quota = Mock()
        
        flow = AutonomousFlow(browser, evaluate, send, seen, logger, stop, quota)
        
        # Act
        results = flow.run(
            your_profile="Test",
            criteria="Test",
            template="Hi",
            mode="ai",
            limit=10,
            shadow_mode=False,
        )
        
        # Assert
        assert results["total_evaluated"] == 0
        assert results["total_sent"] == 0
        assert results["total_skipped"] == 0
        
        # Should not have tried to click any profiles
        browser.click_view_profile.assert_not_called()
        evaluate.assert_not_called()
        send.assert_not_called()
        
        # Should log the stop event
        logger.emit.assert_any_call({"event": "stopped", "at_profile": 0, "reason": "stop_flag"})

    def test_stop_flag_during_run_halts_immediately(self) -> None:
        """If STOP flag appears during run, should halt at next check."""
        # Arrange
        browser = Mock()
        browser.open = Mock()
        browser.click_view_profile = Mock(return_value=True)
        browser.read_profile_text = Mock(side_effect=["Profile 1", "Profile 2"])
        browser.skip = Mock()
        
        evaluate = Mock(return_value={"decision": "NO", "rationale": "No match"})
        send = Mock()
        seen = Mock()
        seen.is_seen = Mock(return_value=False)
        seen.mark_seen = Mock()
        
        logger = Mock()
        
        # STOP flag appears after first profile
        stop = Mock()
        stop.is_stopped = Mock(side_effect=[False, True])
        
        quota = Mock()
        
        flow = AutonomousFlow(browser, evaluate, send, seen, logger, stop, quota)
        
        # Act
        results = flow.run(
            your_profile="Test",
            criteria="Test",
            template="Hi",
            mode="ai",
            limit=10,
            shadow_mode=False,
        )
        
        # Assert
        assert results["total_evaluated"] == 1  # Only processed one
        assert results["total_sent"] == 0
        
        # Should have evaluated exactly one profile
        evaluate.assert_called_once()
        
        # Should log the stop event
        logger.emit.assert_any_call({"event": "stopped", "at_profile": 1, "reason": "stop_flag"})