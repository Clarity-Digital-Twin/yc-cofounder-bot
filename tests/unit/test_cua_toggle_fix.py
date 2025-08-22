"""Test that CUA toggle fix works correctly."""

import os
from unittest.mock import Mock, patch

from yc_matcher.interface.di import build_services


class TestCUAToggleFix:
    """Test that the CUA toggle from UI overrides environment variables."""

    def test_enable_cua_parameter_overrides_env_false(self) -> None:
        """Test that enable_cua=True works even when env var is False."""
        with patch.dict(os.environ, {"ENABLE_CUA": "0", "OPENAI_API_KEY": "test"}):
            with patch("yc_matcher.infrastructure.openai_cua_browser.OpenAICUABrowser") as mock_cua:
                mock_browser = Mock()
                mock_cua.return_value = mock_browser

                # Pass enable_cua=True to override env var
                eval_use, send_use, logger = build_services(
                    criteria_text="test criteria",
                    enable_cua=True,  # This should override ENABLE_CUA=0
                )

                # Should use CUA browser despite env var being 0
                mock_cua.assert_called_once()
                assert send_use.browser == mock_browser

    def test_enable_cua_parameter_overrides_env_true(self) -> None:
        """Test that enable_cua=False works even when env var is True."""
        with patch.dict(os.environ, {"ENABLE_CUA": "1", "ENABLE_PLAYWRIGHT": "1", "OPENAI_API_KEY": "test"}):
            with patch("yc_matcher.infrastructure.browser_playwright_async.PlaywrightBrowserAsync") as mock_playwright:
                mock_browser = Mock()
                mock_playwright.return_value = mock_browser

                # Pass enable_cua=False to override env var
                eval_use, send_use, logger = build_services(
                    criteria_text="test criteria",
                    enable_cua=False,  # This should override ENABLE_CUA=1
                )

                # Should use Playwright browser despite env var being 1
                mock_playwright.assert_called_once()
                assert send_use.browser == mock_browser

    def test_enable_cua_none_uses_env_var(self) -> None:
        """Test that enable_cua=None falls back to env var."""
        with patch.dict(os.environ, {"ENABLE_CUA": "1", "OPENAI_API_KEY": "test"}):
            with patch("yc_matcher.infrastructure.openai_cua_browser.OpenAICUABrowser") as mock_cua:
                mock_browser = Mock()
                mock_cua.return_value = mock_browser

                # Pass enable_cua=None to use env var
                eval_use, send_use, logger = build_services(
                    criteria_text="test criteria",
                    enable_cua=None,  # Should use env var ENABLE_CUA=1
                )

                # Should use CUA browser based on env var
                mock_cua.assert_called_once()
                assert send_use.browser == mock_browser

    def test_enable_cua_not_passed_uses_env_var(self) -> None:
        """Test that not passing enable_cua falls back to env var."""
        with patch.dict(os.environ, {"ENABLE_CUA": "0", "ENABLE_PLAYWRIGHT": "1", "OPENAI_API_KEY": "test"}):
            with patch("yc_matcher.infrastructure.browser_playwright_async.PlaywrightBrowserAsync") as mock_playwright:
                mock_browser = Mock()
                mock_playwright.return_value = mock_browser

                # Don't pass enable_cua at all
                eval_use, send_use, logger = build_services(
                    criteria_text="test criteria",
                    # enable_cua not passed - should use env var
                )

                # Should use Playwright browser based on env var
                mock_playwright.assert_called_once()
                assert send_use.browser == mock_browser
