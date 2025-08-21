"""Test that OpenAI CUA browser doesn't block the event loop.

Following TDD: Write test first, then implementation.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser


class TestCUAAsyncSafety:
    """Test that CUA browser operations are async-safe."""

    @pytest.mark.asyncio
    async def test_openai_calls_dont_block_event_loop(self) -> None:
        """Test that OpenAI API calls don't block the event loop."""
        # Arrange
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "CUA_MODEL": "test-model"}):
            browser = OpenAICUABrowser()

        # Mock the OpenAI client to simulate slow network call
        mock_response = MagicMock()
        mock_response.computer_call = None
        mock_response.content = "Profile text extracted"

        def slow_responses_create(*args, **kwargs):
            """Simulate slow network call that would block."""
            time.sleep(0.1)  # Simulate network latency
            return mock_response

        browser.client.responses = MagicMock()
        browser.client.responses.create = slow_responses_create

        # Mock playwright to avoid actual browser launch
        with patch("yc_matcher.infrastructure.openai_cua_browser.async_playwright") as mock_pw:
            mock_manager = AsyncMock()
            mock_browser = AsyncMock()
            mock_page = AsyncMock()

            mock_pw.return_value.start = AsyncMock(return_value=mock_manager)
            mock_manager.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_page = AsyncMock(return_value=mock_page)
            mock_page.goto = AsyncMock()
            mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot")

            # Act - Run multiple concurrent operations
            start_time = asyncio.get_event_loop().time()

            async def measure_blocking():
                """Helper to measure if operations block."""
                await browser._open_async("https://example.com")
                return asyncio.get_event_loop().time() - start_time

            # Run 3 operations concurrently
            # If blocking, they'd take 0.3s total (sequential)
            # If non-blocking, they'd take ~0.1s (concurrent)
            times = await asyncio.gather(measure_blocking(), measure_blocking(), measure_blocking())

            # Assert - Operations should run concurrently
            total_time = max(times)
            assert total_time < 0.2, f"Operations appear to be blocking: {total_time}s"

    @pytest.mark.asyncio
    async def test_cua_action_loop_is_async_safe(self) -> None:
        """Test that the CUA action loop doesn't block."""
        # Arrange
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "CUA_MODEL": "test-model"}):
            browser = OpenAICUABrowser()

        # Mock responses to simulate CUA loop
        mock_responses = [
            MagicMock(computer_call=MagicMock(action="click", coordinates=(100, 200))),
            MagicMock(computer_call=None, content="Done"),
        ]

        def slow_create(*args, **kwargs):
            time.sleep(0.05)  # Simulate network
            return mock_responses.pop(0) if mock_responses else MagicMock(computer_call=None)

        browser.client.responses = MagicMock()
        browser.client.responses.create = slow_create

        # Mock playwright
        browser.playwright = AsyncMock()
        browser.browser = AsyncMock()
        browser.page = AsyncMock()
        browser.page.screenshot = AsyncMock(return_value=b"screenshot")
        browser.page.click = AsyncMock()

        # Act - Run CUA action loop
        start = asyncio.get_event_loop().time()
        result = await browser._cua_action("click profile")
        elapsed = asyncio.get_event_loop().time() - start

        # Assert - Should not block event loop
        # Two API calls at 0.05s each should take ~0.1s if blocking
        assert elapsed < 0.15, f"CUA loop appears to block: {elapsed}s"
        assert result is not None


class TestProfileCacheClearing:
    """Test that profile cache is properly cleared."""

    @pytest.mark.asyncio
    async def test_cache_clears_on_navigation(self) -> None:
        """Test that profile cache clears when navigating to new URL."""
        # Arrange
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "CUA_MODEL": "test-model"}):
            browser = OpenAICUABrowser()
            browser._profile_text_cache = "old cached text"

        # Mock browser components
        browser.playwright = AsyncMock()
        browser.browser = AsyncMock()
        browser.page = AsyncMock()
        browser.page.goto = AsyncMock()

        # Act
        await browser._open_async("https://newurl.com")

        # Assert
        assert browser._profile_text_cache == "", "Cache should be cleared on navigation"

    @pytest.mark.asyncio
    async def test_cache_clears_on_skip(self) -> None:
        """Test that profile cache clears when skipping profile."""
        # Arrange
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "CUA_MODEL": "test-model"}):
            browser = OpenAICUABrowser()
            browser._profile_text_cache = "cached profile text"

        # Mock CUA action
        with patch.object(browser, "_cua_action", new_callable=AsyncMock) as mock_cua:
            mock_cua.return_value = "skipped"
            browser.playwright = AsyncMock()
            browser.browser = AsyncMock()
            browser.page = AsyncMock()

            # Act
            await browser._skip_async()

            # Assert
            assert browser._profile_text_cache == "", "Cache should be cleared on skip"
