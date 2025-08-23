"""Test OpenAI CUA Browser implementation following TDD principles.

Tests FIRST, implementation after. Testing the Responses API integration
with Playwright executor pattern.
"""

import base64
from pathlib import Path
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
        page.mouse.click = AsyncMock()
        page.close = AsyncMock()
        # Mock evaluate to always return a URL by default
        page.evaluate = AsyncMock(return_value="https://example.com")
        
        # Mock locator chain for read_profile_text
        locator_mock = AsyncMock()
        locator_mock.count = AsyncMock(return_value=1)
        locator_mock.inner_text = AsyncMock(return_value="Profile text here")
        locator_mock.first = locator_mock  # Chain for .first
        page.locator = Mock(return_value=locator_mock)
        page.inner_text = AsyncMock(return_value="Profile text here")  # Fallback

        browser = AsyncMock()
        browser.new_page = AsyncMock(return_value=page)
        browser.close = AsyncMock()

        chromium = AsyncMock()
        chromium.launch = AsyncMock(return_value=browser)

        playwright = AsyncMock()
        playwright.chromium = chromium
        playwright.stop = AsyncMock()

        # Create async context manager
        async_pw = AsyncMock()
        async_pw.__aenter__ = AsyncMock(return_value=playwright)
        async_pw.__aexit__ = AsyncMock()
        async_pw.start = AsyncMock(return_value=playwright)

        return async_pw, playwright, page

    @pytest.fixture
    def mock_env(self, monkeypatch) -> None:
        """Set required environment variables."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("CUA_MODEL", "computer-use-preview")

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
            assert browser.client is not None
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
                "yc_matcher.infrastructure.async_loop_runner.async_playwright",
                return_value=async_pw_mock,
            ):
                browser = OpenAICUABrowser()

                # Act - ensure browser launches
                page = await browser._ensure_browser()

                # Assert - Page is returned
                assert page is not None
                # The AsyncLoopRunner handles the browser internally
                # We can't directly access playwright/browser/page as they're internal

    @pytest.mark.asyncio
    async def test_cua_screenshot_loop_with_computer_call_output(
        self, mock_openai_client: Mock, mock_playwright: tuple, mock_env: None
    ) -> None:
        """Test the core CUA loop: screenshot → analyze → execute → computer_call_output."""
        # Arrange
        async_pw_mock, playwright_mock, page_mock = mock_playwright

        # Mock CUA response with computer_call in output array (correct API structure)
        mock_response = Mock()
        mock_response.id = "resp_123"
        computer_call = Mock(
            type="computer_call",
            call_id="call_456",
            action=Mock(type="click", coordinates={"x": 100, "y": 200}),
            pending_safety_checks=[],  # Explicitly set to empty list
        )
        mock_response.output = [computer_call]

        # Mock follow-up response after computer_call_output
        mock_follow = Mock()
        mock_follow.id = "resp_789"
        mock_follow.output = []  # No more computer calls

        mock_openai_client.responses.create.side_effect = [mock_response, mock_follow]

        with patch(
            "yc_matcher.infrastructure.openai_cua_browser.OpenAI", return_value=mock_openai_client
        ):
            with patch(
                "yc_matcher.infrastructure.async_loop_runner.async_playwright",
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
                assert "input" in second_call.kwargs
                assert second_call.kwargs["input"][0]["type"] == "computer_call_output"
                assert second_call.kwargs["input"][0]["call_id"] == "call_456"
                assert "output" in second_call.kwargs["input"][0]
                assert second_call.kwargs["input"][0]["output"]["type"] == "input_image"

    @pytest.mark.asyncio
    async def test_cua_executes_actions_with_playwright(
        self, mock_openai_client: Mock, mock_playwright: tuple, mock_env: None
    ) -> None:
        """Test that CUA actions are executed via Playwright."""
        # Arrange
        async_pw_mock, playwright_mock, page_mock = mock_playwright

        # Mock different action types (correct API structure)
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
        type_response = Mock(
            id="resp_2",
            output=[
                Mock(
                    type="computer_call",
                    call_id="call_2",
                    action=Mock(type="type", text="Hello World"),
                    pending_safety_checks=[],
                )
            ],
        )
        done_response = Mock(id="resp_3", output=[])  # No more computer calls

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
                "yc_matcher.infrastructure.async_loop_runner.async_playwright",
                return_value=async_pw_mock,
            ):
                browser = OpenAICUABrowser()

                # Patch _ensure_browser to return our test mock
                with patch.object(
                    browser, "_ensure_browser", new_callable=AsyncMock
                ) as mock_ensure:
                    mock_ensure.return_value = page_mock

                    # Act - test click
                    await browser._cua_action("Click button")
                    page_mock.mouse.click.assert_called_once_with(100, 200)

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
                output=[
                    Mock(
                        type="computer_call",
                        call_id="call_1",
                        action=Mock(type="click", coordinates={"x": 50, "y": 50}),
                        pending_safety_checks=[],
                    )
                ],
            ),
            Mock(
                id="resp_2",
                output=[
                    Mock(
                        type="computer_call",
                        call_id="call_2",
                        action=Mock(type="click", coordinates={"x": 100, "y": 100}),
                        pending_safety_checks=[],
                    )
                ],
            ),
            Mock(id="resp_3", output=[]),  # No more computer calls
        ]

        mock_openai_client.responses.create.side_effect = responses

        with patch(
            "yc_matcher.infrastructure.openai_cua_browser.OpenAI", return_value=mock_openai_client
        ):
            with patch(
                "yc_matcher.infrastructure.async_loop_runner.async_playwright",
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

    def test_browser_port_methods_use_cua_loop(
        self, mock_openai_client: Mock, mock_playwright: tuple, mock_env: None
    ) -> None:
        """Test that high-level browser methods use the CUA loop."""
        # Arrange
        async_pw_mock, playwright_mock, page_mock = mock_playwright

        with patch(
            "yc_matcher.infrastructure.openai_cua_browser.OpenAI", return_value=mock_openai_client
        ):
            with patch(
                "yc_matcher.infrastructure.async_loop_runner.async_playwright",
                return_value=async_pw_mock,
            ):
                browser = OpenAICUABrowser()
                
                # Mock the runner's submit method to return expected value
                mock_runner = Mock()
                mock_runner.submit.return_value = "Profile text here"
                browser._runner = mock_runner

                # Act - test high-level methods (sync method, no await)
                result = browser.read_profile_text()

                # Assert
                assert result == "Profile text here"
                mock_runner.submit.assert_called_once()

    def test_fallback_to_playwright_when_cua_fails(
        self, mock_openai_client: Mock, mock_playwright: tuple, mock_env: None
    ) -> None:
        """Test that browser falls back to Playwright when CUA fails."""
        # Arrange
        async_pw_mock, playwright_mock, page_mock = mock_playwright
        mock_openai_client.responses.create.side_effect = Exception("API Error")

        with patch(
            "yc_matcher.infrastructure.openai_cua_browser.OpenAI", return_value=mock_openai_client
        ):
            with patch(
                "yc_matcher.infrastructure.async_loop_runner.async_playwright",
                return_value=async_pw_mock,
            ):
                browser = OpenAICUABrowser()
                browser.fallback_enabled = True  # Enable fallback
                # Inject the page mock for test mode
                browser._page_mock = page_mock

                # Act - should fall back to Playwright (sync method, no await)
                browser.open("https://example.com")

                # Assert - Playwright was used directly
                page_mock.goto.assert_called_once_with("https://example.com")

    def test_required_environment_variables(self, monkeypatch) -> None:
        """Test that missing environment variables raise clear errors."""
        # Arrange - no env vars set
        monkeypatch.delenv("CUA_MODEL", raising=False)

        # Act & Assert
        with pytest.raises(ValueError, match="No Computer Use model available"):
            with patch("yc_matcher.infrastructure.openai_cua_browser.OpenAI"):
                OpenAICUABrowser()

    @pytest.mark.asyncio
    async def test_screenshot_encoding_for_computer_call_output(
        self, mock_openai_client: Mock, mock_playwright: tuple, mock_env: None
    ) -> None:
        """Test that screenshots are properly base64 encoded for computer_call_output."""
        # Arrange
        async_pw_mock, playwright_mock, page_mock = mock_playwright
        screenshot_bytes = b"fake_screenshot_bytes"
        page_mock.screenshot.return_value = screenshot_bytes

        with patch(
            "yc_matcher.infrastructure.openai_cua_browser.OpenAI", return_value=mock_openai_client
        ):
            with patch(
                "yc_matcher.infrastructure.async_loop_runner.async_playwright",
                return_value=async_pw_mock,
            ):
                browser = OpenAICUABrowser()
                # Inject the page mock for test mode
                browser._page_mock = page_mock

                # Act - test screenshot action directly
                result = await browser._cua_action({"type": "screenshot"})

                # Assert - screenshot was base64 encoded
                assert isinstance(result, str)
                # Decode and verify
                decoded = base64.b64decode(result)
                assert decoded == screenshot_bytes

    @pytest.mark.asyncio
    async def test_stop_flag_halts_cua_loop(
        self, mock_openai_client: Mock, mock_playwright: tuple, mock_env: None
    ) -> None:
        """Test that STOP flag properly halts the CUA loop."""
        # Arrange
        async_pw_mock, playwright_mock, page_mock = mock_playwright

        # Mock response with computer_call
        mock_response = Mock(
            id="resp_1",
            output=[
                Mock(
                    type="computer_call",
                    call_id="call_1",
                    action=Mock(type="click", coordinates={"x": 10, "y": 20}),
                    pending_safety_checks=[],
                )
            ],
        )
        mock_openai_client.responses.create.return_value = mock_response

        # Create STOP flag file
        stop_file = Path(".runs/stop.flag")
        stop_file.parent.mkdir(exist_ok=True)
        stop_file.touch()

        try:
            with patch(
                "yc_matcher.infrastructure.openai_cua_browser.OpenAI",
                return_value=mock_openai_client,
            ):
                with patch(
                    "yc_matcher.infrastructure.async_loop_runner.async_playwright",
                    return_value=async_pw_mock,
                ):
                    browser = OpenAICUABrowser()
                    browser.logger = Mock()

                    # Act
                    result = await browser._cua_action("Test action")

                    # Assert - loop should stop and log
                    assert result is None
                    browser.logger.log_event.assert_called_with(
                        "stopped",
                        {"event": "stopped", "where": "_cua_action", "reason": "stop_flag"},
                    )
                    # Should only make initial call, not computer_call_output
                    assert mock_openai_client.responses.create.call_count == 1
        finally:
            # Clean up
            if stop_file.exists():
                stop_file.unlink()

    @pytest.mark.asyncio
    async def test_safety_checks_require_hil_acknowledgment(
        self, mock_openai_client: Mock, mock_playwright: tuple, mock_env: None
    ) -> None:
        """Test that safety checks require HIL acknowledgment."""
        # Arrange
        async_pw_mock, playwright_mock, page_mock = mock_playwright

        # Mock response with safety check
        mock_response = Mock(
            id="resp_1",
            output=[
                Mock(
                    type="computer_call",
                    call_id="call_1",
                    action=Mock(type="click", coordinates={"x": 10, "y": 20}),
                    pending_safety_checks=[
                        Mock(
                            id="safety_1", code="CONFIRM_ACTION", message="Confirm sending message?"
                        )
                    ],
                )
            ],
        )
        mock_openai_client.responses.create.return_value = mock_response

        with patch(
            "yc_matcher.infrastructure.openai_cua_browser.OpenAI", return_value=mock_openai_client
        ):
            with patch(
                "yc_matcher.infrastructure.async_loop_runner.async_playwright",
                return_value=async_pw_mock,
            ):
                browser = OpenAICUABrowser()
                browser.logger = Mock()

                # HIL callback that rejects
                browser.hil_approve_callback = AsyncMock(return_value=False)

                # Act
                result = await browser._cua_action("Send message")

                # Assert - should stop due to safety check rejection
                assert result is None
                browser.hil_approve_callback.assert_called_once()
                # Check that log_event was called with safety_check_not_acknowledged
                browser.logger.log_event.assert_called_once()
                call_args = browser.logger.log_event.call_args
                assert call_args[0][0] == "stopped"
                assert call_args[0][1]["event"] == "stopped"
                assert call_args[0][1]["reason"] == "safety_check_not_acknowledged"
                assert "safety_check" in call_args[0][1]

    def test_verify_sent_strict_checking(
        self, mock_openai_client: Mock, mock_playwright: tuple, mock_env: None
    ) -> None:
        """Test that verify_sent only returns True for explicit confirmation."""
        # Arrange
        async_pw_mock, playwright_mock, page_mock = mock_playwright

        # Mock locator for sent indicators
        locator_mock = Mock()  # Use regular Mock, not AsyncMock
        page_mock.locator = Mock(return_value=locator_mock)  # Make locator synchronous

        with patch(
            "yc_matcher.infrastructure.openai_cua_browser.OpenAI", return_value=mock_openai_client
        ):
            with patch(
                "yc_matcher.infrastructure.async_loop_runner.async_playwright",
                return_value=async_pw_mock,
            ):
                browser = OpenAICUABrowser()
                # Inject the page mock for test mode
                browser._page_mock = page_mock

                # Test case 1: Sent indicator found in DOM
                # Make count a regular function that returns value directly
                locator_mock.count = Mock(return_value=1)
                result = browser.verify_sent()
                assert result is True

                # Test case 2: No sent indicator in DOM
                locator_mock.count = Mock(return_value=0)
                result = browser.verify_sent()
                assert result is False

                # Test case 3: Exception during check (also returns False)
                locator_mock.count = Mock(side_effect=Exception("DOM error"))
                result = browser.verify_sent()
                assert result is False
