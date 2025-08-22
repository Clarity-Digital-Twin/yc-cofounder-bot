"""Test Recent Events panel - Clean, focused tests following Uncle Bob's principles."""

import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest


class TestRecentEventsPanel:
    """Test suite for Recent Events panel functionality.

    Following Clean Code principles:
    - Single Responsibility: Each test checks ONE thing
    - Clear naming: Test names describe what they test
    - No magic: Explicit setup and assertions
    - Fast: All tests run in milliseconds
    """

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    @patch("yc_matcher.interface.web.ui_streamlit.Path")
    @patch("yc_matcher.interface.web.ui_streamlit.os.path.exists")
    def test_empty_events_file_does_not_crash(self, mock_exists: Mock, mock_path: Mock, mock_st: Mock) -> None:
        """Empty events file should show 'No recent events' without crashing."""
        # Arrange - Empty file exists
        mock_exists.return_value = True
        mock_path.return_value.read_text.return_value = ""

        # Setup expander as a proper context manager
        mock_expander = Mock()
        mock_expander.__enter__ = Mock(return_value=mock_expander)
        mock_expander.__exit__ = Mock(return_value=None)
        mock_st.expander.return_value = mock_expander

        # Setup columns as context managers too
        mock_cols = []
        for _ in range(3):
            col = Mock()
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
            mock_cols.append(col)
        mock_st.columns.return_value = mock_cols
        mock_st.button.return_value = False  # No button clicks

        # Import here to trigger the code
        from yc_matcher.interface.web.ui_streamlit import render_events_panel

        # Act - Should not raise exception
        try:
            render_events_panel()
        except NameError as e:
            if "recent_events" in str(e):
                pytest.fail(f"recent_events not defined when file is empty: {e}")

        # Assert - Should show empty state message (but actually renders inside expander)
        # Since empty string goes to 'not content' branch, it shows "No recent events"
        mock_st.info.assert_called_with("No recent events")

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    @patch("yc_matcher.interface.web.ui_streamlit.Path")
    def test_unix_timestamp_format_handled(self, mock_path: Mock, mock_st: Mock) -> None:
        """Events with Unix timestamp ('ts' field) should be displayed correctly."""
        # Arrange - Event with Unix timestamp
        now_unix = datetime.now().timestamp()
        event = {"ts": now_unix, "event": "test_event", "data": "test"}
        mock_path.return_value.read_text.return_value = json.dumps(event)
        # Setup expander as context manager
        mock_expander = Mock()
        mock_expander.__enter__ = Mock(return_value=mock_expander)
        mock_expander.__exit__ = Mock(return_value=None)
        mock_st.expander.return_value = mock_expander
        # Setup columns as context managers
        mock_cols = []
        for _ in range(3):
            col = Mock()
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
            mock_cols.append(col)
        mock_st.columns.return_value = mock_cols
        mock_st.button.return_value = False

        from yc_matcher.interface.web.ui_streamlit import render_events_panel

        # Act
        render_events_panel()

        # Assert - Should show the event (as text since it's not a special type)
        calls = mock_st.text.call_args_list
        assert any("test_event" in str(call) for call in calls)

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    @patch("yc_matcher.interface.web.ui_streamlit.Path")
    def test_iso_timestamp_format_handled(self, mock_path: Mock, mock_st: Mock) -> None:
        """Events with ISO timestamp should be displayed correctly."""
        # Arrange - Event with ISO timestamp
        now_iso = datetime.now().isoformat()
        event = {"timestamp": now_iso, "event": "decision", "data": {"decision": "YES"}}
        mock_path.return_value.read_text.return_value = json.dumps(event)
        # Setup expander as context manager
        mock_expander = Mock()
        mock_expander.__enter__ = Mock(return_value=mock_expander)
        mock_expander.__exit__ = Mock(return_value=None)
        mock_st.expander.return_value = mock_expander
        # Setup columns as context managers
        mock_cols = []
        for _ in range(3):
            col = Mock()
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
            mock_cols.append(col)
        mock_st.columns.return_value = mock_cols
        mock_st.button.return_value = False

        from yc_matcher.interface.web.ui_streamlit import render_events_panel

        # Act
        render_events_panel()

        # Assert - Should display decision
        calls = mock_st.info.call_args_list
        assert any("decision: YES" in str(call) for call in calls)

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    @patch("yc_matcher.interface.web.ui_streamlit.Path")
    def test_old_events_filtered_out(self, mock_path: Mock, mock_st: Mock) -> None:
        """Events older than 1 hour should be filtered out."""
        # Arrange - One old event, one recent
        old_time = (datetime.now() - timedelta(hours=2)).timestamp()
        recent_time = datetime.now().timestamp()

        events = [
            json.dumps({"ts": old_time, "event": "old_event"}),
            json.dumps({"ts": recent_time, "event": "recent_event"})
        ]
        mock_path.return_value.read_text.return_value = "\n".join(events)
        # Setup expander as context manager
        mock_expander = Mock()
        mock_expander.__enter__ = Mock(return_value=mock_expander)
        mock_expander.__exit__ = Mock(return_value=None)
        mock_st.expander.return_value = mock_expander
        # Setup columns as context managers
        mock_cols = []
        for _ in range(3):
            col = Mock()
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
            mock_cols.append(col)
        mock_st.columns.return_value = mock_cols
        mock_st.button.return_value = False

        from yc_matcher.interface.web.ui_streamlit import render_events_panel

        # Act
        render_events_panel()

        # Assert - Only recent event should be shown (as text since it's generic)
        text_calls = [str(call) for call in mock_st.text.call_args_list]
        assert any("recent_event" in call for call in text_calls)
        assert not any("old_event" in call for call in text_calls)

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    @patch("yc_matcher.interface.web.ui_streamlit.Path")
    def test_malformed_json_does_not_crash(self, mock_path: Mock, mock_st: Mock) -> None:
        """Malformed JSON lines should be skipped without crashing."""
        # Arrange - Mix of valid and invalid JSON
        events = [
            "not valid json",
            json.dumps({"ts": datetime.now().timestamp(), "event": "valid_event"}),
            "{broken json",
        ]
        mock_path.return_value.read_text.return_value = "\n".join(events)
        # Setup expander as context manager
        mock_expander = Mock()
        mock_expander.__enter__ = Mock(return_value=mock_expander)
        mock_expander.__exit__ = Mock(return_value=None)
        mock_st.expander.return_value = mock_expander
        # Setup columns as context managers
        mock_cols = []
        for _ in range(3):
            col = Mock()
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
            mock_cols.append(col)
        mock_st.columns.return_value = mock_cols
        mock_st.button.return_value = False

        from yc_matcher.interface.web.ui_streamlit import render_events_panel

        # Act - Should not raise exception
        render_events_panel()

        # Assert - Valid event should still be shown (as text since it's generic)
        text_calls = [str(call) for call in mock_st.text.call_args_list]
        assert any("valid_event" in call for call in text_calls)

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    @patch("yc_matcher.interface.web.ui_streamlit.os.path.exists")
    def test_missing_events_file_handled_gracefully(self, mock_exists: Mock, mock_st: Mock) -> None:
        """Missing events file should not show the panel at all."""
        # Arrange
        mock_exists.return_value = False

        from yc_matcher.interface.web.ui_streamlit import render_events_panel

        # Act
        render_events_panel()

        # Assert - Should not try to create expander
        mock_st.expander.assert_not_called()


class TestEventsPanelButtons:
    """Test the Clear and Refresh buttons functionality."""

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    @patch("yc_matcher.interface.web.ui_streamlit.Path")
    @patch("builtins.open", create=True)
    def test_clear_button_empties_file(self, mock_open: Mock, mock_path: Mock, mock_st: Mock) -> None:
        """Clear button should empty the events file."""
        # Arrange
        mock_path.return_value.read_text.return_value = '{"event": "test"}'
        # Setup expander as context manager
        mock_expander = Mock()
        mock_expander.__enter__ = Mock(return_value=mock_expander)
        mock_expander.__exit__ = Mock(return_value=None)
        mock_st.expander.return_value = mock_expander
        # Setup columns as context managers
        mock_cols = []
        for _ in range(3):
            col = Mock()
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
            mock_cols.append(col)
        mock_st.columns.return_value = mock_cols
        mock_st.button.side_effect = [False, True]  # Refresh=False, Clear=True

        from yc_matcher.interface.web.ui_streamlit import render_events_panel

        # Act
        render_events_panel()

        # Assert - Should write empty string to file
        mock_open.assert_called_with(".runs/events.jsonl", "w")
        handle = mock_open.return_value.__enter__.return_value
        handle.write.assert_called_with("")

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    def test_refresh_button_triggers_rerun(self, mock_st: Mock) -> None:
        """Refresh button should trigger streamlit rerun."""
        # Arrange
        # Setup expander as context manager
        mock_expander = Mock()
        mock_expander.__enter__ = Mock(return_value=mock_expander)
        mock_expander.__exit__ = Mock(return_value=None)
        mock_st.expander.return_value = mock_expander
        # Setup columns as context managers
        mock_cols = []
        for _ in range(3):
            col = Mock()
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
            mock_cols.append(col)
        mock_st.columns.return_value = mock_cols
        mock_st.button.side_effect = [True, False]  # Refresh=True, Clear=False

        from yc_matcher.interface.web.ui_streamlit import render_events_panel

        # Act
        render_events_panel()

        # Assert
        mock_st.rerun.assert_called_once()
