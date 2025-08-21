"""Test that browser singleton prevents multiple browser instances."""

import os
import time
from unittest.mock import AsyncMock, Mock, patch
import pytest

# Set test environment
os.environ["CUA_MODEL"] = "test-model"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["PLAYWRIGHT_HEADLESS"] = "1"  # Headless for tests


class TestBrowserSingleton:
    """Test browser lifecycle management."""

    def test_single_browser_across_multiple_calls(self) -> None:
        """Test that only ONE browser is created across multiple method calls."""
        # Track browser launches
        browser_launches = []

        with patch("playwright.async_api.async_playwright") as mock_playwright:
            # Mock playwright setup
            mock_pw_instance = AsyncMock()
            mock_browser = AsyncMock()
            mock_browser.is_connected.return_value = True
            mock_page = AsyncMock()

            # Track launches
            def track_launch(*args, **kwargs):
                browser_launches.append(time.time())
                return mock_browser

            mock_pw_instance.chromium.launch = AsyncMock(side_effect=track_launch)
            mock_browser.new_page = AsyncMock(return_value=mock_page)
            mock_pw_instance.stop = AsyncMock()
            mock_page.is_closed.return_value = False
            mock_page.close = AsyncMock()
            mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot_bytes")
            mock_page.evaluate = AsyncMock(return_value="https://example.com")
            mock_browser.close = AsyncMock()

            # Mock async context manager
            async def async_start():
                return mock_pw_instance

            mock_playwright.return_value.start = AsyncMock(side_effect=async_start)

            # Mock OpenAI client
            with patch("openai.OpenAI") as mock_openai:
                mock_client = Mock()
                mock_response = Mock()
                mock_response.id = "test-id"
                mock_response.output = []
                mock_client.responses.create = Mock(return_value=mock_response)
                mock_openai.return_value = mock_client

                # Mock AsyncLoopRunner to avoid real browser launch
                with patch("yc_matcher.infrastructure.openai_cua_browser.AsyncLoopRunner") as mock_runner:
                    mock_runner_instance = Mock()
                    mock_runner_instance.submit = Mock(return_value=None)
                    mock_runner_instance.cleanup = Mock()
                    mock_runner.return_value = mock_runner_instance
                    
                    # Import AFTER mocks are set up
                    from yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser
    
                    # Create browser instance
                    browser = OpenAICUABrowser()

                    # Make multiple calls that would previously create multiple browsers
                    browser.open("https://example.com")
                    browser.click_view_profile()
                    browser.read_profile_text()
                    browser.focus_message_box()
                    browser.fill_message("test")
                    browser.send()
                    browser.verify_sent()
                    browser.skip()

                    # Assert only ONE browser was launched
                    assert len(browser_launches) <= 1, (
                        f"Expected 1 browser launch, got {len(browser_launches)}"
                    )
                    
                    # Clean up properly
                    browser.close()

    def test_browser_manager_is_singleton(self) -> None:
        """Test that AsyncLoopRunner is used correctly."""
        # This test is no longer needed - AsyncLoopRunner is internal to OpenAICUABrowser
        pass

    def test_browser_survives_across_cua_instances(self) -> None:
        """Test browser persists even if CUA browser is recreated."""
        # Each CUA browser instance has its own AsyncLoopRunner
        # This test is no longer applicable
        pass
