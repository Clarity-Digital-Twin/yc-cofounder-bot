"""Clean UI tests with minimal mocking - no sprawl, high signal."""

from unittest.mock import Mock, patch


def _cm():
    """Create a mock that works as a context manager."""
    m = Mock()
    m.__enter__ = Mock(return_value=m)
    m.__exit__ = Mock(return_value=None)
    return m


class TestUIStreamlitClean:
    """Clean tests for Streamlit UI components."""

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    @patch("yc_matcher.interface.web.ui_streamlit.config")
    def test_start_requires_inputs(self, mock_config: Mock, mock_st: Mock) -> None:
        """Test that Start button requires both profile and criteria."""
        # 1) columns/expander behave as context managers
        mock_st.expander.return_value = _cm()

        # columns returns different number based on input
        def columns_side_effect(spec):
            if isinstance(spec, int):
                return [_cm() for _ in range(spec)]
            elif isinstance(spec, list):
                return [_cm() for _ in range(len(spec))]
            return [_cm(), _cm(), _cm()]  # default

        mock_st.columns.side_effect = columns_side_effect

        # 2) simplest defaults for UI calls used before the guard
        mock_st.toggle.return_value = False
        mock_st.number_input.return_value = 10
        mock_st.set_page_config.return_value = None
        mock_st.title.return_value = None
        mock_st.subheader.return_value = None
        mock_st.markdown.return_value = None
        mock_st.info.return_value = None
        mock_st.success.return_value = None
        mock_st.error.return_value = None
        mock_st.caption.return_value = None
        mock_st.code.return_value = None
        mock_st.metric.return_value = None

        # 3) three text areas — profile / criteria empty, template present
        mock_st.text_area.side_effect = ["", "", "template"]
        mock_st.button.return_value = False  # not clicking Start

        # Session state
        mock_st.session_state = {"hil_pending": None}

        # 4) config getters shouldn't trigger anything heavy
        mock_config.is_headless.return_value = True
        mock_config.get_playwright_browsers_path.return_value = "/tmp"
        mock_config.get_cua_model.return_value = None
        mock_config.get_cua_max_turns.return_value = 40
        mock_config.get_pace_seconds.return_value = 45
        mock_config.get_auto_browse_limit.return_value = 10
        mock_config.is_shadow_mode.return_value = False
        mock_config.get_decision_model.return_value = "gpt-4o"
        mock_config.use_three_input_ui.return_value = True
        mock_config.is_cua_enabled.return_value = False
        mock_config.is_playwright_enabled.return_value = True
        mock_config.get_auto_send_default.return_value = False
        mock_config.get_yc_credentials.return_value = ("user@example.com", "x")

        from yc_matcher.interface.web.ui_streamlit import render_three_input_mode

        render_three_input_mode()

        # Should warn and not run
        mock_st.warning.assert_called_with(
            "Please fill both your profile and match criteria to start."
        )
        # No exceptions = pass

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    @patch("yc_matcher.interface.web.ui_streamlit.config")
    def test_valid_inputs_shows_start_button(self, mock_config: Mock, mock_st: Mock) -> None:
        """Test that valid inputs allow Start button to appear."""
        # Setup context managers
        mock_st.expander.return_value = _cm()

        # columns returns different number based on input
        def columns_side_effect(spec):
            if isinstance(spec, int):
                return [_cm() for _ in range(spec)]
            elif isinstance(spec, list):
                return [_cm() for _ in range(len(spec))]
            return [_cm(), _cm(), _cm()]  # default

        mock_st.columns.side_effect = columns_side_effect

        # UI defaults
        mock_st.toggle.return_value = False
        mock_st.number_input.return_value = 20
        mock_st.set_page_config.return_value = None
        mock_st.title.return_value = None
        mock_st.subheader.return_value = None
        mock_st.markdown.return_value = None
        mock_st.button.return_value = False

        # Session state - no pending HIL check
        mock_st.session_state = {"hil_pending": None}

        # Valid inputs
        mock_st.text_area.side_effect = ["Technical founder", "Business co-founder", "template"]

        # Config
        mock_config.is_headless.return_value = True
        mock_config.get_playwright_browsers_path.return_value = None
        mock_config.get_cua_model.return_value = "test-model"
        mock_config.get_cua_max_turns.return_value = 40
        mock_config.get_pace_seconds.return_value = 45
        mock_config.get_auto_browse_limit.return_value = 20
        mock_config.is_shadow_mode.return_value = False
        mock_config.get_decision_model.return_value = "gpt-4o"
        mock_config.is_cua_enabled.return_value = False
        mock_config.is_playwright_enabled.return_value = True
        mock_config.get_auto_send_default.return_value = False
        mock_config.get_yc_credentials.return_value = ("", "")
        mock_config.use_three_input_ui.return_value = True

        from yc_matcher.interface.web.ui_streamlit import render_three_input_mode

        render_three_input_mode()

        # The code shows system status which may include warnings - that's OK
        # Just verify the Start button is available
        # Should show Start button
        button_calls = [str(call) for call in mock_st.button.call_args_list]
        assert any("Start Autonomous Browsing" in call for call in button_calls)


class TestEventsPanelClean:
    """Clean tests for events panel."""

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    @patch("yc_matcher.interface.web.ui_streamlit.Path")
    @patch("yc_matcher.interface.web.ui_streamlit.os.path.exists")
    def test_events_empty_file(self, mock_exists: Mock, mock_path: Mock, mock_st: Mock) -> None:
        """Test empty events file shows 'No events in the last hour'."""
        mock_exists.return_value = True
        mock_path.return_value.read_text.return_value = ""  # empty file

        # context managers
        mock_st.expander.return_value = _cm()

        def columns_side_effect(spec):
            if isinstance(spec, int):
                return [_cm() for _ in range(spec)]
            elif isinstance(spec, list):
                return [_cm() for _ in range(len(spec))]
            return [_cm(), _cm()]  # default

        mock_st.columns.side_effect = columns_side_effect
        mock_st.button.return_value = False

        from yc_matcher.interface.web.ui_streamlit import render_events_panel

        render_events_panel()

        # When file is empty, shows this message
        mock_st.info.assert_called_with(
            "No events in the last hour. Events are cleared after 1 hour."
        )

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    @patch("yc_matcher.interface.web.ui_streamlit.Path")
    @patch("yc_matcher.interface.web.ui_streamlit.os.path.exists")
    def test_events_ts_only(self, mock_exists: Mock, mock_path: Mock, mock_st: Mock) -> None:
        """Test event with Unix timestamp only gets normalized and displayed."""
        import json
        import time

        mock_exists.return_value = True
        event = {"ts": time.time(), "event": "test_event"}
        mock_path.return_value.read_text.return_value = json.dumps(event)
        mock_st.expander.return_value = _cm()

        def columns_side_effect(spec):
            if isinstance(spec, int):
                return [_cm() for _ in range(spec)]
            elif isinstance(spec, list):
                return [_cm() for _ in range(len(spec))]
            return [_cm(), _cm()]  # default

        mock_st.columns.side_effect = columns_side_effect
        mock_st.button.return_value = False

        from yc_matcher.interface.web.ui_streamlit import render_events_panel

        render_events_panel()

        # generic event → st.text line rendered
        assert any("test_event" in str(c) for c in mock_st.text.call_args_list)

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    @patch("yc_matcher.interface.web.ui_streamlit.Path")
    @patch("yc_matcher.interface.web.ui_streamlit.os.path.exists")
    def test_events_decision_yes(self, mock_exists: Mock, mock_path: Mock, mock_st: Mock) -> None:
        """Test decision YES event shows as info."""
        import json
        import time

        mock_exists.return_value = True
        event = {"ts": time.time(), "event": "decision", "data": {"decision": "YES"}}
        mock_path.return_value.read_text.return_value = json.dumps(event)
        mock_st.expander.return_value = _cm()

        def columns_side_effect(spec):
            if isinstance(spec, int):
                return [_cm() for _ in range(spec)]
            elif isinstance(spec, list):
                return [_cm() for _ in range(len(spec))]
            return [_cm(), _cm()]  # default

        mock_st.columns.side_effect = columns_side_effect
        mock_st.button.return_value = False

        from yc_matcher.interface.web.ui_streamlit import render_events_panel

        render_events_panel()

        # Decision YES → st.info with thumbs up
        info_calls = [str(c) for c in mock_st.info.call_args_list]
        assert any("decision: YES" in call for call in info_calls)
