"""Test UI input validation guard - minimal and focused."""

from unittest.mock import Mock, patch


class TestUIInputsGuard:
    """Test that UI properly validates inputs before allowing start."""

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    def test_empty_inputs_shows_warning_no_button(self, mock_st: Mock) -> None:
        """With empty inputs, should show warning and not show Start button."""
        # Arrange
        mock_st.text_area.side_effect = ["", "", "template"]  # Empty profile and criteria
        mock_st.button.return_value = False

        # Mock columns to support context manager protocol and unpacking
        def make_col_mock():
            col = Mock()
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
            return col

        # Return correct number based on input - columns(3) or columns([1,4]) etc
        def columns_side_effect(spec):
            n = spec if isinstance(spec, int) else len(spec)
            return [make_col_mock() for _ in range(n)]

        mock_st.columns.side_effect = columns_side_effect

        from yc_matcher.interface.web.ui_streamlit import render_three_input_mode

        # Act
        render_three_input_mode()

        # Assert - Should show warning
        mock_st.warning.assert_called_with(
            "Please fill both your profile and match criteria to start."
        )
        # Should not attempt to show Start button
        assert not any(
            "Start Autonomous Browsing" in str(call) for call in mock_st.button.call_args_list
        )

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    def test_whitespace_only_inputs_shows_warning(self, mock_st: Mock) -> None:
        """Whitespace-only inputs should be treated as empty."""
        # Arrange
        mock_st.text_area.side_effect = ["  \n  ", "  \t  ", "template"]  # Whitespace only
        mock_st.button.return_value = False

        # Mock columns to support context manager protocol and unpacking
        def make_col_mock():
            col = Mock()
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
            return col

        # Return correct number based on input - columns(3) or columns([1,4]) etc
        def columns_side_effect(spec):
            n = spec if isinstance(spec, int) else len(spec)
            return [make_col_mock() for _ in range(n)]

        mock_st.columns.side_effect = columns_side_effect

        from yc_matcher.interface.web.ui_streamlit import render_three_input_mode

        # Act
        render_three_input_mode()

        # Assert
        mock_st.warning.assert_called_with(
            "Please fill both your profile and match criteria to start."
        )

    @patch("yc_matcher.interface.web.ui_streamlit.st")
    @patch("yc_matcher.interface.web.ui_streamlit.config")
    def test_valid_inputs_shows_start_button(self, mock_config: Mock, mock_st: Mock) -> None:
        """With valid inputs, should show Start button."""
        # Arrange
        mock_st.text_area.side_effect = ["Technical founder", "Business cofounder", "template"]
        mock_st.button.return_value = False  # Don't actually click
        mock_st.toggle.return_value = False
        mock_st.number_input.return_value = 20

        # Mock columns to support context manager protocol and unpacking
        def make_col_mock():
            col = Mock()
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
            return col

        # Return correct number based on input - columns(3) or columns([1,4]) etc
        def columns_side_effect(spec):
            n = spec if isinstance(spec, int) else len(spec)
            return [make_col_mock() for _ in range(n)]

        mock_st.columns.side_effect = columns_side_effect
        mock_config.is_headless.return_value = True
        mock_config.get_cua_model.return_value = "test-model"
        mock_config.get_yc_credentials.return_value = ("", "")  # Empty but valid tuple

        from yc_matcher.interface.web.ui_streamlit import render_three_input_mode

        # Act
        render_three_input_mode()

        # Assert - Should show Start button
        button_calls = [
            call
            for call in mock_st.button.call_args_list
            if "Start Autonomous Browsing" in str(call)
        ]
        assert len(button_calls) > 0, "Start button should be shown with valid inputs"
