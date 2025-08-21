"""Test Streamlit UI components with minimal mocks following TDD."""

from typing import Any
from unittest.mock import Mock, patch

import pytest

from yc_matcher.interface.web.ui_streamlit import render_three_input_mode, render_paste_mode


class TestStreamlitUI:
    """Test suite for Streamlit UI components."""

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    def test_render_three_input_mode_sets_page_config(self, mock_st: Mock) -> None:
        """Test that 3-input mode sets correct page configuration."""
        # Arrange
        mock_st.session_state = {}
        mock_st.columns.return_value = [Mock(), Mock(), Mock()]
        mock_st.button.return_value = False
        mock_st.text_area.return_value = ""
        mock_st.selectbox.return_value = "hybrid"
        mock_st.number_input.return_value = 10
        mock_st.toggle.return_value = False
        mock_st.slider.return_value = 0.7
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()

        # Act
        render_three_input_mode()

        # Assert
        mock_st.set_page_config.assert_called_once_with(
            page_title="YC Matcher (Autonomous Mode)", layout="wide"
        )
        mock_st.title.assert_called_once_with("🚀 YC Co-Founder Matcher - Autonomous Mode")

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    def test_three_input_mode_initializes_session_state(self, mock_st: Mock) -> None:
        """Test that session state is properly initialized."""
        # Arrange
        mock_st.session_state = {}
        mock_st.columns.return_value = [Mock(), Mock(), Mock()]
        mock_st.button.return_value = False
        mock_st.text_area.return_value = ""
        mock_st.selectbox.return_value = "hybrid"
        mock_st.number_input.return_value = 10
        mock_st.toggle.return_value = False
        mock_st.slider.return_value = 0.7
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()

        # Act
        render_three_input_mode()

        # Assert - session state should be initialized
        assert "hil_pending" in mock_st.session_state
        assert "last_screenshot" in mock_st.session_state

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    def test_three_input_mode_creates_three_columns(self, mock_st: Mock) -> None:
        """Test that UI creates three input columns."""
        # Arrange
        mock_st.session_state = {"hil_pending": None, "last_screenshot": None}
        mock_cols = [Mock(), Mock(), Mock()]
        mock_st.columns.return_value = mock_cols
        mock_st.button.return_value = False
        mock_st.text_area.return_value = ""
        mock_st.selectbox.return_value = "hybrid"
        mock_st.number_input.return_value = 10
        mock_st.toggle.return_value = False
        mock_st.slider.return_value = 0.7
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()

        # Act
        render_three_input_mode()

        # Assert
        mock_st.columns.assert_any_call(3)  # Main input columns
        # Verify text areas were created for all three inputs
        assert mock_st.text_area.call_count >= 3

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    def test_decision_mode_selector_options(self, mock_st: Mock) -> None:
        """Test that decision mode selector has correct options."""
        # Arrange
        mock_st.session_state = {"hil_pending": None, "last_screenshot": None}
        mock_st.columns.return_value = [Mock(), Mock(), Mock()]
        mock_st.button.return_value = False
        mock_st.text_area.return_value = ""
        mock_st.number_input.return_value = 10
        mock_st.toggle.return_value = False
        mock_st.slider.return_value = 0.7
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()

        # Act
        render_three_input_mode()

        # Assert - selectbox should be called with correct modes
        mock_st.selectbox.assert_called_once()
        call_args = mock_st.selectbox.call_args
        assert call_args[0][0] == "Decision Mode"
        assert set(call_args[0][1]) == {"advisor", "rubric", "hybrid"}

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    @patch("yc_matcher.interface.web.ui_streamlit.FileStopFlag")
    def test_stop_flag_control(self, mock_stop_flag_class: Mock, mock_st: Mock) -> None:
        """Test STOP flag control functionality."""
        # Arrange
        mock_stop = Mock()
        mock_stop.is_stopped.return_value = False
        mock_stop_flag_class.return_value = mock_stop
        
        mock_st.session_state = {"hil_pending": None, "last_screenshot": None}
        mock_st.columns.side_effect = [
            [Mock(), Mock(), Mock()],  # Main inputs
            [Mock(), Mock(), Mock()],  # Config
            [Mock(), Mock()],  # Stop control
        ]
        mock_st.button.side_effect = [False, False]  # STOP button, Clear button
        mock_st.text_area.return_value = ""
        mock_st.selectbox.return_value = "hybrid"
        mock_st.number_input.return_value = 10
        mock_st.toggle.return_value = False
        mock_st.slider.return_value = 0.7
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()

        # Act
        render_three_input_mode()

        # Assert
        mock_stop_flag_class.assert_called_once()
        mock_stop.is_stopped.assert_called()

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    def test_hil_safety_panel_appears_when_pending(self, mock_st: Mock) -> None:
        """Test HIL safety check panel appears when pending."""
        # Arrange
        mock_st.session_state = {
            "hil_pending": {"message": "Safety check required", "id": "123"},
            "last_screenshot": None
        }
        mock_st.columns.return_value = [Mock(), Mock(), Mock()]
        mock_st.button.return_value = False
        mock_st.text_area.return_value = ""
        mock_st.selectbox.return_value = "hybrid"
        mock_st.number_input.return_value = 10
        mock_st.toggle.return_value = False
        mock_st.slider.return_value = 0.7
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()
        mock_warning = Mock()
        mock_st.warning.return_value.__enter__ = Mock(return_value=mock_warning)
        mock_st.warning.return_value.__exit__ = Mock()

        # Act
        render_three_input_mode()

        # Assert
        mock_st.warning.assert_called_once_with("⚠️ Safety Check Required")
        mock_st.code.assert_called_with("Safety check required")

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    def test_screenshot_panel_displays_when_available(self, mock_st: Mock) -> None:
        """Test screenshot panel displays when screenshot available."""
        # Arrange
        mock_st.session_state = {
            "hil_pending": None,
            "last_screenshot": "base64encodedimage"
        }
        mock_st.columns.return_value = [Mock(), Mock(), Mock()]
        mock_st.button.return_value = False
        mock_st.text_area.return_value = ""
        mock_st.selectbox.return_value = "hybrid"
        mock_st.number_input.return_value = 10
        mock_st.toggle.return_value = False
        mock_st.slider.return_value = 0.7
        mock_expander = Mock()
        mock_expander.__enter__ = Mock(return_value=mock_expander)
        mock_expander.__exit__ = Mock()
        mock_st.expander.return_value = mock_expander

        # Act
        render_three_input_mode()

        # Assert
        mock_st.expander.assert_any_call("📸 Last Screenshot", expanded=False)
        mock_st.image.assert_called_once_with(
            "data:image/png;base64,base64encodedimage",
            use_column_width=True
        )

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    @patch("yc_matcher.interface.web.ui_streamlit.build_services")
    def test_start_button_validates_inputs(self, mock_build: Mock, mock_st: Mock) -> None:
        """Test that start button validates required inputs."""
        # Arrange
        mock_st.session_state = {"hil_pending": None, "last_screenshot": None}
        mock_st.columns.return_value = [Mock(), Mock(), Mock()]
        mock_st.button.side_effect = [False, False, True]  # Start button pressed
        mock_st.text_area.side_effect = ["", "criteria", "template"]  # Empty profile
        mock_st.selectbox.return_value = "hybrid"
        mock_st.number_input.return_value = 10
        mock_st.toggle.return_value = False
        mock_st.slider.return_value = 0.7
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()

        # Act
        render_three_input_mode()

        # Assert
        mock_st.error.assert_called_once_with("Please fill in Your Profile and Match Criteria")
        mock_build.assert_not_called()

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    def test_render_paste_mode_sets_page_config(self, mock_st: Mock) -> None:
        """Test paste mode sets correct page configuration."""
        # Arrange
        mock_st.sidebar.__enter__ = Mock()
        mock_st.sidebar.__exit__ = Mock()
        mock_st.text_area.return_value = ""
        mock_st.number_input.return_value = 5
        mock_st.toggle.return_value = True
        mock_st.button.return_value = False
        mock_st.columns.return_value = [Mock(), Mock()]

        # Act
        render_paste_mode()

        # Assert
        mock_st.set_page_config.assert_called_once_with(
            page_title="YC Matcher (Paste & Evaluate)", layout="wide"
        )

    @patch("yc_matcher.interface.web.ui_streamlit.os")
    @patch("yc_matcher.interface.web.ui_streamlit.render_three_input_mode")
    @patch("yc_matcher.interface.web.ui_streamlit.render_paste_mode")
    def test_main_selects_mode_based_on_env(
        self, mock_paste: Mock, mock_three: Mock, mock_os: Mock
    ) -> None:
        """Test main() selects UI mode based on environment variable."""
        from yc_matcher.interface.web.ui_streamlit import main

        # Test three-input mode
        mock_os.getenv.return_value = "true"
        main()
        mock_three.assert_called_once()
        mock_paste.assert_not_called()

        # Reset mocks
        mock_three.reset_mock()
        mock_paste.reset_mock()

        # Test paste mode (default)
        mock_os.getenv.return_value = "false"
        main()
        mock_paste.assert_called_once()
        mock_three.assert_not_called()