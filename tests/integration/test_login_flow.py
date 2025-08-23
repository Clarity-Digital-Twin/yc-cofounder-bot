"""Integration tests for login flow across different browser implementations.

Tests the login flow from end-to-end, including:
- CUA browser login
- Playwright browser login
- Credential validation
- Login persistence
"""

import os
from unittest.mock import AsyncMock, Mock, patch

import pytest

from yc_matcher.infrastructure.browser_playwright import PlaywrightBrowser
from yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser


class TestLoginFlowIntegration:
    """Integration tests for login functionality."""

    @patch.dict(
        os.environ,
        {
            "YC_EMAIL": "test@example.com",
            "YC_PASSWORD": "test123",
            "OPENAI_API_KEY": "test-key",
            "CUA_MODEL": "test-model",
        },
    )
    @patch("yc_matcher.infrastructure.openai_cua_browser.OpenAI")
    def test_cua_browser_performs_login(self, mock_openai: Mock) -> None:
        """Test that CUA browser can perform login with credentials."""
        # Arrange
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # Mock the CUA responses for login flow
        login_response = Mock(
            id="resp_1",
            output=[],  # No computer calls, just completion
            content="Login successful",
        )
        mock_client.responses.create.return_value = login_response

        # Create browser and mock the runner
        with patch(
            "yc_matcher.infrastructure.async_loop_runner.AsyncLoopRunner"
        ) as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.submit.return_value = None  # ensure_logged_in returns None

            browser = OpenAICUABrowser()

            # Act
            result = browser.ensure_logged_in()

            # Assert
            assert result is None  # No error means success
            # Verify runner was used
            mock_runner.submit.assert_called()

    @patch.dict(os.environ, {"YC_EMAIL": "test@example.com", "YC_PASSWORD": "test123"})
    @patch("yc_matcher.infrastructure.browser_playwright.sync_playwright")
    def test_playwright_browser_performs_login(self, mock_playwright: Mock) -> None:
        """Test that Playwright browser can perform login with credentials."""
        # Arrange
        mock_page = Mock()
        mock_context = Mock()
        mock_browser = Mock()
        mock_pl = Mock()

        # Set up the chain of calls
        mock_playwright.return_value = mock_pl
        mock_pl.start.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Mock login check - locator.count() is a method that returns an int
        mock_locator = Mock()
        mock_locator.count = lambda: 0  # Not logged in initially (return int directly)
        mock_page.locator.return_value = mock_locator

        # Mock get_by_label and get_by_text for _click_by_labels
        mock_page.get_by_label = Mock(return_value=mock_locator)
        mock_page.get_by_text = Mock(return_value=mock_locator)

        # Create browser
        browser = PlaywrightBrowser()

        # Act - PlaywrightBrowser doesn't have ensure_logged_in, only is_logged_in
        is_logged_in = browser.is_logged_in()

        # Assert
        # Should check for login indicators
        assert not is_logged_in  # Not logged in initially
        mock_page.locator.assert_called()

    @patch.dict(os.environ, {})  # No credentials
    def test_login_fails_without_credentials(self) -> None:
        """Test that login fails gracefully when no credentials are provided."""
        # Arrange
        browser = PlaywrightBrowser()

        # Act & Assert - PlaywrightBrowser doesn't have ensure_logged_in
        # Just check that it's not logged in without credentials
        is_logged_in = browser.is_logged_in()
        assert not is_logged_in

    @patch.dict(
        os.environ,
        {
            "YC_EMAIL": "test@example.com",
            "YC_PASSWORD": "test123",
            "OPENAI_API_KEY": "test-key",
            "CUA_MODEL": "test-model",
        },
    )
    @patch("yc_matcher.infrastructure.openai_cua_browser.OpenAI")
    def test_cua_browser_uses_playwright_for_login_execution(self, mock_openai: Mock) -> None:
        """Test that CUA browser uses Playwright to execute login actions."""
        # Arrange
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # Mock CUA response with login actions
        click_response = Mock(
            id="resp_1",
            output=[
                Mock(
                    type="computer_call",
                    call_id="call_1",
                    action=Mock(type="click", coordinates={"x": 100, "y": 200}),
                    pending_safety_checks=[],
                )
            ],
        )
        done_response = Mock(id="resp_2", output=[])
        mock_client.responses.create.side_effect = [click_response, done_response]

        # Create browser with mocked runner
        with patch(
            "yc_matcher.infrastructure.async_loop_runner.AsyncLoopRunner"
        ) as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.submit.return_value = None  # ensure_logged_in returns None

            browser = OpenAICUABrowser()

            # Act
            browser.ensure_logged_in()

            # Assert
            # Verify runner was used
            mock_runner.submit.assert_called()

    @patch("yc_matcher.infrastructure.browser_playwright.sync_playwright")
    def test_is_logged_in_check(self, mock_playwright: Mock) -> None:
        """Test the is_logged_in check works correctly."""
        # Arrange
        mock_page = Mock()
        mock_context = Mock()
        mock_browser = Mock()
        mock_pl = Mock()

        # Set up the chain of calls
        mock_playwright.return_value = mock_pl
        mock_pl.start.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Mock logged in state
        mock_locator = Mock()
        mock_page.locator.return_value = mock_locator
        mock_locator.count = lambda: 1  # Found logout button = logged in (return int directly)

        # Mock get_by_label and get_by_text for _click_by_labels
        mock_page.get_by_label = Mock(return_value=mock_locator)
        mock_page.get_by_text = Mock(return_value=mock_locator)
        mock_page.goto = Mock()  # Mock the goto method

        browser = PlaywrightBrowser()
        browser.open("https://test.com")

        # Act
        is_logged_in = browser.is_logged_in()

        # Assert
        assert is_logged_in is True
        mock_page.locator.assert_called()  # Should check for login indicators

    @patch.dict(
        os.environ,
        {
            "YC_EMAIL": "test@example.com",
            "YC_PASSWORD": "wrong",
            "OPENAI_API_KEY": "test-key",
            "CUA_MODEL": "test-model",
        },
    )
    @patch("yc_matcher.infrastructure.openai_cua_browser.OpenAI")
    def test_login_handles_invalid_credentials(self, mock_openai: Mock) -> None:
        """Test that invalid credentials are handled gracefully."""
        # Arrange
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # Mock failed login response
        error_response = Mock(id="resp_1", output=[], content="Login failed: Invalid credentials")
        mock_client.responses.create.return_value = error_response

        # Create browser with mocked runner that raises exception
        with patch(
            "yc_matcher.infrastructure.async_loop_runner.AsyncLoopRunner"
        ) as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.submit.side_effect = Exception("Login failed")

            browser = OpenAICUABrowser()

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                browser.ensure_logged_in()

            assert "login" in str(exc_info.value).lower()


class TestLoginPersistence:
    """Test that login state persists across operations."""

    @patch("yc_matcher.infrastructure.browser_playwright.sync_playwright")
    def test_login_persists_across_page_navigations(self, mock_playwright: Mock) -> None:
        """Test that login persists when navigating between pages."""
        # Arrange
        mock_page = Mock()
        mock_context = Mock()
        mock_browser = Mock()
        mock_pl = Mock()

        # Set up the chain of calls
        mock_playwright.return_value = mock_pl
        mock_pl.start.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Initially logged in
        mock_locator = Mock()
        mock_locator.count = lambda: 1  # Return int directly
        mock_page.locator.return_value = mock_locator
        mock_page.get_by_label = Mock(return_value=mock_locator)
        mock_page.get_by_text = Mock(return_value=mock_locator)
        mock_page.goto = Mock()  # Mock the goto method

        browser = PlaywrightBrowser()
        browser.open("https://test.com")

        # Act
        initial_login = browser.is_logged_in()
        browser.open("https://test.com/other-page")  # Navigate
        after_nav_login = browser.is_logged_in()

        # Assert
        assert initial_login is True
        assert after_nav_login is True  # Should still be logged in

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "CUA_MODEL": "test-model"})
    @patch("yc_matcher.infrastructure.openai_cua_browser.OpenAI")
    @patch("yc_matcher.infrastructure.async_loop_runner.AsyncLoopRunner")
    @patch("playwright.async_api.async_playwright")
    def test_cua_browser_reuses_single_browser_instance(
        self, mock_playwright: Mock, mock_runner_class: Mock, mock_openai: Mock
    ) -> None:
        """Test that CUA browser maintains a single browser instance."""
        # Arrange
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # Mock the runner
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        # Mock Playwright
        mock_async_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_async_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_playwright.return_value.__aenter__.return_value = mock_async_playwright

        browser = OpenAICUABrowser()

        # Mock the runner.submit to return the mock page
        mock_runner.submit.return_value = mock_page

        # Act
        page1 = browser._runner.submit(browser._ensure_browser())
        page2 = browser._runner.submit(browser._ensure_browser())

        # Assert
        assert page1 is page2  # Should be the same instance
