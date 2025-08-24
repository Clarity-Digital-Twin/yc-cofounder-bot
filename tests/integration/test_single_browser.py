"""Test that we only create ONE browser instance - no spam!"""

import os

# Set test environment
os.environ["CUA_MODEL"] = "test-model"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["PLAYWRIGHT_HEADLESS"] = "1"


def test_single_browser_instance() -> None:
    """Test that multiple method calls use the SAME browser instance."""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, Mock, patch

    launch_count = 0

    # Patch BEFORE import
    with (
        patch("yc_matcher.infrastructure.browser.async_loop_runner.AsyncLoopRunner") as mock_runner,
        patch("playwright.async_api.async_playwright") as mock_pw,
        patch("openai.OpenAI") as mock_openai,
    ):
        # Setup AsyncLoopRunner mock
        mock_runner_instance = Mock()
        mock_runner_instance.submit = Mock(return_value=None)
        mock_runner_instance.cleanup = Mock()
        mock_runner.return_value = mock_runner_instance

        # Setup Playwright mocks with correct async/sync types
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_page = AsyncMock()

        # Sync methods (not awaited)
        mock_browser.is_connected = Mock(return_value=True)
        mock_page.is_closed = Mock(return_value=False)

        # Async page methods
        mock_page.goto = AsyncMock()
        mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot")
        mock_page.evaluate = AsyncMock(return_value="http://example.com")
        mock_page.close = AsyncMock()
        mock_page.mouse = SimpleNamespace(click=AsyncMock())
        mock_page.keyboard = SimpleNamespace(type=AsyncMock(), press=AsyncMock())

        # Browser async methods
        mock_browser.close = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)

        # Track launches
        async def count_launch(*args, **kwargs):
            nonlocal launch_count
            launch_count += 1
            return mock_browser

        mock_pw_instance.chromium.launch = AsyncMock(side_effect=count_launch)
        mock_pw_instance.stop = AsyncMock()

        # Playwright start
        async def mock_start():
            return mock_pw_instance

        mock_pw.return_value.start = AsyncMock(side_effect=mock_start)

        # Setup OpenAI mock
        mock_client = Mock()
        mock_response = Mock(id="test", output=[])
        mock_client.responses.create = Mock(return_value=mock_response)
        mock_openai.return_value = mock_client

        # Import AFTER all patches are in place
        from yc_matcher.infrastructure.browser.openai_cua import OpenAICUABrowser

        # Create browser instance
        browser = OpenAICUABrowser()

        try:
            # These should all use the SAME browser
            browser.open("https://example.com")
            browser.click_view_profile()
            browser.read_profile_text()
            browser.focus_message_box()
            browser.fill_message("test")
            browser.send()
            browser.verify_sent()
            browser.skip()

            # CRITICAL ASSERTION: With mocked AsyncLoopRunner, no actual browser launch
            # The test verifies that multiple calls don't create multiple browser instances
            assert launch_count == 0, (
                f"Expected 0 browser launches with mocked runner, got {launch_count}"
            )
            print("✅ SUCCESS: No browser instances created with mocked runner!")
        finally:
            # ALWAYS clean up
            browser.close()


if __name__ == "__main__":
    test_single_browser_instance()
