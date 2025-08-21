"""Test that STOP flag is checked before sending messages.

Following TDD: Write test first, then implementation.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yc_matcher.application.use_cases import SendMessage
from yc_matcher.application.ports import StopController


class TestStopCheckBeforeSend:
    """Test that STOP flag is properly checked before sending."""

    def test_stop_flag_prevents_send(self, tmp_path: Path) -> None:
        """Test that STOP flag prevents message from being sent."""
        # Arrange
        mock_browser = MagicMock()
        mock_quota = MagicMock()
        mock_quota.check_and_increment.return_value = True
        mock_logger = MagicMock()
        mock_stop = MagicMock()
        
        # Create stop flag behavior
        mock_stop.is_stopped.return_value = True
        
        with patch.dict('os.environ', {'PACE_MIN_SECONDS': '0'}):
            send_message = SendMessage(
                browser=mock_browser,
                quota=mock_quota,
                logger=mock_logger,
                stop=mock_stop  # Need to add this parameter
            )
            
            # Act
            result = send_message(
                draft="Test message",
                limit=100
            )
            
            # Assert - Should not send when stop flag exists
            assert result is False, "Should return False when stop flag exists"
            mock_browser.focus_message_box.assert_not_called()
            mock_browser.fill_message.assert_not_called()
            mock_browser.send.assert_not_called()
    
    def test_stop_flag_checked_after_focus_before_fill(self, tmp_path: Path) -> None:
        """Test that STOP flag is checked between focus and fill operations."""
        # Arrange
        mock_browser = MagicMock()
        mock_quota = MagicMock()
        mock_quota.check_and_increment.return_value = True
        mock_logger = MagicMock()
        mock_stop = MagicMock()
        
        # Stop flag appears after focus
        # Checks: start, before_focus, after_focus 
        stop_states = [False, False, True]  # Stop after focus
        mock_stop.is_stopped.side_effect = stop_states
        
        with patch.dict('os.environ', {'PACE_MIN_SECONDS': '0'}):
            send_message = SendMessage(
                browser=mock_browser,
                quota=mock_quota,
                logger=mock_logger,
                stop=mock_stop
            )
            
            # Act
            result = send_message(
                draft="Test message",
                limit=100
            )
            
            # Assert - Should stop after focus but before fill
            assert result is False, "Should return False when stop flag appears"
            mock_browser.focus_message_box.assert_called_once()
            mock_browser.fill_message.assert_not_called()
            mock_browser.send.assert_not_called()
    
    def test_stop_flag_checked_before_actual_send(self, tmp_path: Path) -> None:
        """Test that STOP flag is checked right before sending."""
        # Arrange
        mock_browser = MagicMock()
        mock_quota = MagicMock()
        mock_quota.check_and_increment.return_value = True
        mock_logger = MagicMock()
        mock_stop = MagicMock()
        
        # Stop flag appears after fill
        # Checks: start, before_focus, after_focus, before_send
        stop_states = [False, False, False, True]  # Stop before send
        mock_stop.is_stopped.side_effect = stop_states
        
        with patch.dict('os.environ', {'PACE_MIN_SECONDS': '0'}):
            send_message = SendMessage(
                browser=mock_browser,
                quota=mock_quota,
                logger=mock_logger,
                stop=mock_stop
            )
            
            # Act
            result = send_message(
                draft="Test message",
                limit=100
            )
            
            # Assert - Should stop after fill but before send
            assert result is False, "Should return False when stop flag appears"
            mock_browser.focus_message_box.assert_called_once()
            mock_browser.fill_message.assert_called_once()
            mock_browser.send.assert_not_called()
    
    def test_normal_send_without_stop_flag(self, tmp_path: Path) -> None:
        """Test that messages are sent normally without stop flag."""
        # Arrange
        mock_browser = MagicMock()
        mock_browser.verify_sent.return_value = True
        mock_quota = MagicMock()
        mock_quota.check_and_increment.return_value = True
        mock_logger = MagicMock()
        mock_stop = MagicMock()
        mock_stop.is_stopped.return_value = False  # Never stopped
        
        with patch.dict('os.environ', {'PACE_MIN_SECONDS': '0'}):
            send_message = SendMessage(
                browser=mock_browser,
                quota=mock_quota,
                logger=mock_logger,
                stop=mock_stop
            )
            
            # Act
            result = send_message(
                draft="Test message",
                limit=100
            )
            
            # Assert - Should send normally
            assert result is True, "Should return True when message sent"
            mock_browser.focus_message_box.assert_called_once()
            mock_browser.fill_message.assert_called_once_with("Test message")
            mock_browser.send.assert_called_once()
            mock_browser.verify_sent.assert_called_once()