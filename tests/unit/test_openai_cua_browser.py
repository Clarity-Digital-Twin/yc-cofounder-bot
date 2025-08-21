"""Test OpenAI CUA Browser implementation following TDD principles.

Tests FIRST, implementation after. Testing the Responses API integration
with Playwright executor pattern.
"""

import base64
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Test the interface we WANT, not what exists
from yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser


class TestOpenAICUABrowserResponsesAPI:
    """Test CUA uses Responses API with Playwright executor."""

    @pytest.fixture
    def mock_openai_client(self) -> Mock:
        """Mock OpenAI client for Responses API."""
        client = Mock()
        client.responses = Mock()
        client.responses.create = Mock()
        return client

    @pytest.fixture
    def mock_playwright(self) -> AsyncMock:
        """Mock Playwright for browser control."""
        page = AsyncMock()
        page.screenshot = AsyncMock(return_value=b"fake_screenshot_bytes")
        page.goto = AsyncMock()
        page.click = AsyncMock()
        page.fill = AsyncMock()
        page.keyboard = AsyncMock()
        page.keyboard.type = AsyncMock()
        page.keyboard.press = AsyncMock()
        page.mouse = AsyncMock()
        page.mouse.wheel = AsyncMock()
        page.close = AsyncMock()

        browser = AsyncMock()
        browser.new_page = AsyncMock(return_value=page)
        browser.close = AsyncMock()

        chromium = AsyncMock()
        chromium.launch = AsyncMock(return_value=browser)

        playwright = AsyncMock()
        playwright.chromium = chromium
        playwright.stop = AsyncMock()
        playwright.start = AsyncMock(return_value=playwright)

        # async_playwright returns a context manager
        async_pw_mock = AsyncMock()
        async_pw_mock.start = AsyncMock(return_value=playwright)

        return async_pw_mock, playwright, page

    @pytest.fixture
    def mock_env(self, monkeypatch) -> None:
        """Setup required environment variables."""
        monkeypatch.setenv("CUA_MODEL", "computer-use-preview")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("CUA_TEMPERATURE", "0.3")

    @pytest.mark.asyncio
    async def test_cua_browser_uses_responses_api_not_agents_sdk(
        self, mock_openai_client: Mock, mock_env: None
    ) -> None:
        """Test that CUA browser uses Responses API, not Agents SDK."""
        # Arrange
        with patch(
            "yc_matcher.infrastructure.openai_cua_browser.OpenAI", return_value=mock_openai_client
        ):
            browser = OpenAICUABrowser()

            # Act - verify initialization
            assert browser.client == mock_openai_client
            assert browser.model == "computer-use-preview"

            # Assert - no Agents SDK imports
            assert not hasattr(browser, "agent")  # No Agent from SDK
            assert not hasattr(browser, "session")  # No Session from SDK

    @pytest.mark.asyncio
    async def test_cua_integrates_playwright_for_execution(
        self, mock_openai_client: Mock, mock_playwright: tuple, mock_env: None
    ) -> None:
        """Test that CUA uses Playwright to execute actions."""
        # Arrange
        async_pw_mock, playwright_mock, page_mock = mock_playwright

        with patch(
            "yc_matcher.infrastructure.openai_cua_browser.OpenAI", return_value=mock_openai_client
        ):
            with patch(
                "yc_matcher.infrastructure.openai_cua_browser.async_playwright",
                return_value=async_pw_mock,
            ):
                browser = OpenAICUABrowser()

                # Act - ensure browser launches
                await browser._ensure_browser()

                # Assert - Playwright is initialized
                assert browser.playwright is not None
                assert browser.page == page_mock
                playwright_mock.chromium.launch.assert_called_once()

    @pytest.mark.asyncio
    async def test_cua_screenshot_loop_with_computer_call_output(
        self, mock_openai_client: Mock, mock_playwright: tuple, mock_env: None
    ) -> None:
        """Test the core CUA loop: screenshot → analyze → execute → computer_call_output."""
        # Arrange
        async_pw_mock, playwright_mock, page_mock = mock_playwright
        
        # Add evaluate mock for URL checking
        page_mock.evaluate = AsyncMock(return_value="https://example.com")
        page_mock.mouse.click = AsyncMock()  # Add mouse.click for coordinates

        # Mock CUA response with computer_call in output array (correct API structure)
        mock_response = Mock()
        mock_response.id = "resp_123"
        mock_response.output = [
            Mock(
                type="computer_call",
                call_id="call_456",
                action=Mock(type="click", coordinates={"x": 100, "y": 200})
            )
        ]

        # Mock follow-up response after computer_call_output
        mock_follow = Mock()
        mock_follow.id = "resp_789"
        mock_follow.output = []  # No more computer calls

        mock_openai_client.responses.create.side_effect = [mock_response, mock_follow]

        with patch(
            "yc_matcher.infrastructure.openai_cua_browser.OpenAI", return_value=mock_openai_client
        ):
            with patch(
                "yc_matcher.infrastructure.openai_cua_browser.async_playwright",
                return_value=async_pw_mock,
            ):
                browser = OpenAICUABrowser()

                # Act
                await browser._cua_action("Click the first profile")

                # Assert - proper API calls
                assert mock_openai_client.responses.create.call_count == 2

                # First call: initial request with tools
                first_call = mock_openai_client.responses.create.call_args_list[0]
                assert first_call.kwargs["model"] == "computer-use-preview"
                assert first_call.kwargs["truncation"] == "auto"
                assert any(t["type"] == "computer_use_preview" for t in first_call.kwargs["tools"])

                # Second call: computer_call_output with screenshot
                second_call = mock_openai_client.responses.create.call_args_list[1]
                assert second_call.kwargs["previous_response_id"] == "resp_123"
                assert "computer_call_output" in second_call.kwargs
                assert second_call.kwargs["computer_call_output"]["call_id"] == "call_456"
                assert "screenshot" in second_call.kwargs["computer_call_output"]

    @pytest.mark.asyncio
    async def test_cua_executes_actions_with_playwright(
        self, mock_openai_client: Mock, mock_playwright: tuple, mock_env: None
    ) -> None:
        """Test that CUA actions are executed via Playwright."""
        # Arrange
        async_pw_mock, playwright_mock, page_mock = mock_playwright

        # Mock different action types
        click_response = Mock(
            id="resp_1",
            computer_call=Mock(id="call_1", type="click", coordinates={"x": 100, "y": 200}),
        )
        type_response = Mock(
            id="resp_2", computer_call=Mock(id="call_2", type="type", text="Hello World")
        )
        done_response = Mock(id="resp_3", computer_call=None)

        mock_openai_client.responses.create.side_effect = [
            click_response,
            done_response,  # For click test
            type_response,
            done_response,  # For type test
        ]

        with patch(
            "yc_matcher.infrastructure.openai_cua_browser.OpenAI", return_value=mock_openai_client
        ):
            with patch(
                "yc_matcher.infrastructure.openai_cua_browser.async_playwright",
                return_value=async_pw_mock,
            ):
                browser = OpenAICUABrowser()

                # Act - test click
                await browser._cua_action("Click button")
                page_mock.click.assert_called_once_with({"x": 100, "y": 200})

                # Act - test type
                await browser._cua_action("Type message")
                page_mock.keyboard.type.assert_called_once_with("Hello World")

    @pytest.mark.asyncio
    async def test_previous_response_id_chains_turns(
        self, mock_openai_client: Mock, mock_playwright: tuple, mock_env: None
    ) -> None:
        """Test that previous_response_id properly chains conversation turns."""
        # Arrange
        async_pw_mock, playwright_mock, page_mock = mock_playwright

        responses = [
            Mock(
                id="resp_1",
                computer_call=Mock(id="call_1", type="click", coordinates={"x": 50, "y": 50}),
            ),
            Mock(
                id="resp_2",
                computer_call=Mock(id="call_2", type="click", coordinates={"x": 100, "y": 100}),
            ),
            Mock(id="resp_3", computer_call=None),
        ]

        mock_openai_client.responses.create.side_effect = responses

        with patch(
            "yc_matcher.infrastructure.openai_cua_browser.OpenAI", return_value=mock_openai_client
        ):
            with patch(
                "yc_matcher.infrastructure.openai_cua_browser.async_playwright",
                return_value=async_pw_mock,
            ):
                browser = OpenAICUABrowser()

                # Act
                await browser._cua_action("Navigate and click")

                # Assert - verify chaining
                calls = mock_openai_client.responses.create.call_args_list

                # First call has no previous_response_id
                assert calls[0].kwargs.get("previous_response_id") is None

                # Second call (computer_call_output) references first response
                assert calls[1].kwargs["previous_response_id"] == "resp_1"

                # Third call references second response
                assert calls[2].kwargs["previous_response_id"] == "resp_2"

    @pytest.mark.asyncio
    async def test_browser_port_methods_use_cua_loop(
        self, mock_openai_client: Mock, mock_playwright: tuple, mock_env: None
    ) -> None:
        """Test that high-level browser methods use the CUA loop."""
        # Arrange
        async_pw_mock, playwright_mock, page_mock = mock_playwright

        # Mock simple response
        mock_response = Mock(id="resp_1", computer_call=None, output={"text": "Profile text here"})
        mock_openai_client.responses.create.return_value = mock_response

        with patch(
            "yc_matcher.infrastructure.openai_cua_browser.OpenAI", return_value=mock_openai_client
        ):
            with patch(
                "yc_matcher.infrastructure.openai_cua_browser.async_playwright",
                return_value=async_pw_mock,
            ):
                browser = OpenAICUABrowser()

                # Act - test high-level methods
                await browser.open("https://example.com")
                assert mock_openai_client.responses.create.called

                result = await browser.read_profile_text()
                assert result == "Profile text here"

                await browser.fill_message("Test message")
                assert mock_openai_client.responses.create.called

    @pytest.mark.asyncio
    async def test_fallback_to_playwright_when_cua_fails(
        self, mock_openai_client: Mock, mock_playwright: tuple, mock_env: None
    ) -> None:
        """Test graceful fallback to Playwright-only when CUA fails."""
        # Arrange
        async_pw_mock, playwright_mock, page_mock = mock_playwright
        mock_openai_client.responses.create.side_effect = Exception("API Error")

        with patch(
            "yc_matcher.infrastructure.openai_cua_browser.OpenAI", return_value=mock_openai_client
        ):
            with patch(
                "yc_matcher.infrastructure.openai_cua_browser.async_playwright",
                return_value=async_pw_mock,
            ):
                browser = OpenAICUABrowser()
                browser.fallback_enabled = True  # Enable fallback

                # Act - should fall back to Playwright
                await browser.open("https://example.com")

                # Assert - Playwright was used directly
                page_mock.goto.assert_called_once_with("https://example.com")

    def test_required_environment_variables(self, monkeypatch) -> None:
        """Test that missing environment variables raise clear errors."""
        # Arrange - no env vars set
        monkeypatch.delenv("CUA_MODEL", raising=False)

        # Act & Assert
        with pytest.raises(ValueError, match="CUA_MODEL environment variable not set"):
            with patch("yc_matcher.infrastructure.openai_cua_browser.OpenAI"):
                OpenAICUABrowser()

    @pytest.mark.asyncio
    async def test_screenshot_encoding_for_computer_call_output(
        self, mock_openai_client: Mock, mock_playwright: tuple, mock_env: None
    ) -> None:
        """Test that screenshots are properly base64 encoded for computer_call_output."""
        # Arrange
        async_pw_mock, playwright_mock, page_mock = mock_playwright
        screenshot_bytes = b"fake_screenshot_data"
        page_mock.screenshot.return_value = screenshot_bytes

        mock_response = Mock(
            id="resp_1",
            computer_call=Mock(id="call_1", type="click", coordinates={"x": 10, "y": 20}),
        )
        mock_openai_client.responses.create.return_value = mock_response

        with patch(
            "yc_matcher.infrastructure.openai_cua_browser.OpenAI", return_value=mock_openai_client
        ):
            with patch(
                "yc_matcher.infrastructure.openai_cua_browser.async_playwright",
                return_value=async_pw_mock,
            ):
                browser = OpenAICUABrowser()

                # Act
                await browser._cua_action("Click element")

                # Assert - screenshot was encoded
                calls = mock_openai_client.responses.create.call_args_list
                if len(calls) > 1:  # computer_call_output was sent
                    output_call = calls[1]
                    screenshot_b64 = output_call.kwargs["computer_call_output"]["screenshot"]

                    # Verify it's valid base64
                    decoded = base64.b64decode(screenshot_b64)
                    assert decoded == screenshot_bytes
