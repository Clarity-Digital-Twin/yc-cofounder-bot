"""Test that we only create ONE browser instance - no spam!"""

import os

# Set test environment
os.environ["CUA_MODEL"] = "test-model"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["PLAYWRIGHT_HEADLESS"] = "1"


def test_single_browser_instance() -> None:
    """Test that multiple method calls use the SAME browser instance."""
    from unittest.mock import AsyncMock, Mock, patch

    launch_count = 0

    # Mock playwright
    with patch("playwright.async_api.async_playwright") as mock_pw:
        # Track browser launches
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.is_connected.return_value = True
        mock_page = AsyncMock()
        mock_page.is_closed.return_value = False

        # Add async mocks for page methods
        async def mock_goto(*args, **kwargs):
            return None

        async def mock_screenshot(*args, **kwargs):
            return b"fake_screenshot"

        async def mock_evaluate(*args, **kwargs):
            return "http://example.com"

        async def mock_close(*args, **kwargs):
            return None

        mock_page.goto = AsyncMock(side_effect=mock_goto)
        mock_page.screenshot = AsyncMock(side_effect=mock_screenshot)
        mock_page.evaluate = AsyncMock(side_effect=mock_evaluate)
        mock_page.close = AsyncMock(side_effect=mock_close)
        mock_browser.close = AsyncMock(side_effect=mock_close)

        async def count_launch(*args, **kwargs):
            nonlocal launch_count
            launch_count += 1
            return mock_browser

        mock_pw_instance.chromium.launch = AsyncMock(side_effect=count_launch)

        async def mock_stop(*args, **kwargs):
            return None

        mock_pw_instance.stop = AsyncMock(side_effect=mock_stop)

        async def mock_new_page(*args, **kwargs):
            return mock_page

        mock_browser.new_page = AsyncMock(side_effect=mock_new_page)

        async def mock_start():
            return mock_pw_instance

        mock_pw.return_value.start = AsyncMock(side_effect=mock_start)

        # Mock OpenAI
        with patch("openai.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_response = Mock(id="test", output=[])
            mock_client.responses.create = Mock(return_value=mock_response)
            mock_openai.return_value = mock_client

            # Import AFTER mocks
            from yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser

            # Create browser and make multiple calls
            browser = OpenAICUABrowser()

            # These should all use the SAME browser
            browser.open("https://example.com")
            browser.click_view_profile()
            browser.read_profile_text()
            browser.focus_message_box()
            browser.fill_message("test")
            browser.send()
            browser.verify_sent()
            browser.skip()

            # CRITICAL ASSERTION: Only ONE browser launch!
            assert launch_count == 1, f"Expected 1 browser launch, got {launch_count}"
            print(f"✅ SUCCESS: Only {launch_count} browser instance created!")

            # Clean up
            browser.close()


if __name__ == "__main__":
    test_single_browser_instance()
