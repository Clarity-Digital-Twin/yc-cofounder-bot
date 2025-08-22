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

from yc_matcher.infrastructure.browser_playwright import BrowserPlaywright
from yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser


class TestLoginFlowIntegration:
    """Integration tests for login functionality."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"YC_EMAIL": "test@example.com", "YC_PASSWORD": "test123"})
    @patch("yc_matcher.infrastructure.openai_cua_browser.OpenAI")
    async def test_cua_browser_performs_login(self, mock_openai: Mock) -> None:
        """Test that CUA browser can perform login with credentials."""
        # Arrange
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock the CUA responses for login flow
        login_response = Mock(
            id="resp_1",
            output=[],  # No computer calls, just completion
            content="Login successful"
        )
        mock_client.responses.create.return_value = login_response
        
        # Create browser
        browser = OpenAICUABrowser()
        
        # Act
        result = browser.ensure_logged_in()
        
        # Assert
        assert result is None  # No error means success
        # Verify CUA was called to perform login
        mock_client.responses.create.assert_called()
        
    @pytest.mark.asyncio
    @patch.dict(os.environ, {"YC_EMAIL": "test@example.com", "YC_PASSWORD": "test123"})
    @patch("yc_matcher.infrastructure.browser_playwright.sync_playwright")
    def test_playwright_browser_performs_login(self, mock_playwright: Mock) -> None:
        """Test that Playwright browser can perform login with credentials."""
        # Arrange
        mock_context = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        
        mock_playwright.return_value.start.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        # Mock login check
        mock_page.locator.return_value.count.return_value = 0  # Not logged in initially
        
        # Create browser
        browser = BrowserPlaywright()
        
        # Act
        browser.ensure_logged_in()
        
        # Assert
        # Should navigate to login page
        mock_page.goto.assert_called()
        # Should fill email and password
        assert mock_page.fill.call_count >= 2
        # Should click login button
        mock_page.click.assert_called()

    @patch.dict(os.environ, {})  # No credentials
    def test_login_fails_without_credentials(self) -> None:
        """Test that login fails gracefully when no credentials are provided."""
        # Arrange
        browser = BrowserPlaywright()
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            browser.ensure_logged_in()
        
        assert "credentials" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"YC_EMAIL": "test@example.com", "YC_PASSWORD": "test123"})
    @patch("yc_matcher.infrastructure.openai_cua_browser.OpenAI")
    @patch("playwright.async_api.async_playwright")
    async def test_cua_browser_uses_playwright_for_login_execution(
        self, mock_playwright: Mock, mock_openai: Mock
    ) -> None:
        """Test that CUA browser uses Playwright to execute login actions."""
        # Arrange
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock Playwright page
        mock_page = AsyncMock()
        mock_async_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_async_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_playwright.return_value.__aenter__.return_value = mock_async_playwright
        
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
        
        # Create browser
        browser = OpenAICUABrowser()
        
        # Act
        await browser._ensure_logged_in_async()
        
        # Assert
        # Verify Playwright was used to execute the click
        mock_page.mouse.click.assert_called_with(100, 200)

    @patch("yc_matcher.infrastructure.browser_playwright.sync_playwright")
    def test_is_logged_in_check(self, mock_playwright: Mock) -> None:
        """Test the is_logged_in check works correctly."""
        # Arrange
        mock_page = Mock()
        mock_playwright.return_value.start.return_value.chromium.launch.return_value.new_page.return_value = mock_page
        
        # Mock logged in state
        mock_locator = Mock()
        mock_page.locator.return_value = mock_locator
        mock_locator.count.return_value = 1  # Found logout button = logged in
        
        browser = BrowserPlaywright()
        browser.open("https://test.com")
        
        # Act
        is_logged_in = browser.is_logged_in()
        
        # Assert
        assert is_logged_in is True
        mock_page.locator.assert_called()  # Should check for login indicators

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"YC_EMAIL": "test@example.com", "YC_PASSWORD": "wrong"})
    @patch("yc_matcher.infrastructure.openai_cua_browser.OpenAI")
    async def test_login_handles_invalid_credentials(self, mock_openai: Mock) -> None:
        """Test that invalid credentials are handled gracefully."""
        # Arrange
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock failed login response
        error_response = Mock(
            id="resp_1",
            output=[],
            content="Login failed: Invalid credentials"
        )
        mock_client.responses.create.return_value = error_response
        
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
        mock_playwright.return_value.start.return_value.chromium.launch.return_value.new_page.return_value = mock_page
        
        # Initially logged in
        mock_page.locator.return_value.count.return_value = 1
        
        browser = BrowserPlaywright()
        browser.open("https://test.com")
        
        # Act
        initial_login = browser.is_logged_in()
        browser.open("https://test.com/other-page")  # Navigate
        after_nav_login = browser.is_logged_in()
        
        # Assert
        assert initial_login is True
        assert after_nav_login is True  # Should still be logged in

    @pytest.mark.asyncio
    @patch("yc_matcher.infrastructure.openai_cua_browser.OpenAI")
    @patch("playwright.async_api.async_playwright")
    async def test_cua_browser_reuses_single_browser_instance(
        self, mock_playwright: Mock, mock_openai: Mock
    ) -> None:
        """Test that CUA browser maintains a single browser instance."""
        # Arrange
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock Playwright
        mock_async_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_async_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_playwright.return_value.__aenter__.return_value = mock_async_playwright
        
        browser = OpenAICUABrowser()
        
        # Act
        page1 = await browser._ensure_browser()
        page2 = await browser._ensure_browser()
        
        # Assert
        assert page1 is page2  # Should be the same instance
        # Browser should only be launched once
        mock_async_playwright.chromium.launch.assert_called_once()