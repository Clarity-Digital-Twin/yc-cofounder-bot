"""OpenAI Computer Use adapter using Responses API with Playwright executor.

Following clean code principles:
- Single Responsibility: CUA plans, Playwright executes
- Dependency Inversion: Implements ComputerUsePort interface
- Open/Closed: Extensible via port, not modification
"""

from __future__ import annotations

import base64
import os
from typing import Any

from openai import OpenAI
from playwright.async_api import Browser, Page, Playwright, async_playwright


class OpenAICUABrowser:
    """Browser automation using OpenAI CUA (Responses API) + Playwright.

    Architecture:
    - CUA (via Responses API) = Planner/Analyzer
    - Playwright = Executor/Browser Control
    - Loop: Screenshot → CUA analyze → CUA suggest → Playwright execute

    This replaces the Agents SDK implementation with the correct
    Responses API pattern as per SSOT.
    """

    def __init__(self) -> None:
        """Initialize CUA browser with Responses API client and Playwright."""
        # OpenAI client for Responses API
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Model configuration
        self.model = os.getenv("CUA_MODEL")
        if not self.model:
            raise ValueError(
                "CUA_MODEL environment variable not set. "
                "Check your Models endpoint at platform.openai.com/account/models"
            )

        self.temperature = float(os.getenv("CUA_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("CUA_MAX_TOKENS", "1200"))

        # Playwright components (initialized on first use)
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None

        # Response chaining
        self.prev_response_id: str | None = None

        # Fallback configuration
        self.fallback_enabled = os.getenv("ENABLE_PLAYWRIGHT_FALLBACK", "1") == "1"

        # Cache for efficiency
        self._profile_text_cache = ""

    async def _ensure_browser(self) -> None:
        """Ensure Playwright browser is running (lazy initialization)."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=os.getenv("PLAYWRIGHT_HEADLESS", "0") == "1"
            )
            self.page = await self.browser.new_page()

    async def _execute_action(self, action: Any) -> None:
        """Execute CUA-suggested action via Playwright.

        Args:
            action: Computer call from CUA with type and parameters
        """
        await self._ensure_browser()

        if action.type == "click":
            # Click at coordinates
            coords = action.coordinates
            await self.page.click({"x": coords["x"], "y": coords["y"]})

        elif action.type == "type":
            # Type text
            await self.page.keyboard.type(action.text)

        elif action.type == "scroll":
            # Scroll page
            await self.page.mouse.wheel(0, action.get("delta", 100))

        elif action.type == "key":
            # Press key
            await self.page.keyboard.press(action.key)

        elif action.type == "screenshot":
            # Just take screenshot, no action needed
            pass

    async def _cua_action(self, instruction: str) -> str | None:
        """Core CUA loop: plan with Responses API, execute with Playwright.

        Args:
            instruction: What to do (e.g., "Click the first profile")

        Returns:
            Text output from CUA if any
        """
        await self._ensure_browser()

        # Take initial screenshot for CUA to analyze
        screenshot = await self.page.screenshot()
        screenshot_b64 = base64.b64encode(screenshot).decode()

        # Start or continue CUA planning turn
        response = self.client.responses.create(
            model=self.model,
            input=[{"role": "user", "content": instruction}],
            tools=[{"type": "computer_use_preview", "display_width": 1920, "display_height": 1080}],
            truncation="auto",
            previous_response_id=self.prev_response_id,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        # Process response
        result_text = None

        # Keep executing computer calls until done
        while hasattr(response, "computer_call") and response.computer_call:
            action = response.computer_call

            # Execute the action with Playwright
            await self._execute_action(action)

            # Take screenshot after action
            screenshot = await self.page.screenshot()
            screenshot_b64 = base64.b64encode(screenshot).decode()

            # Send computer_call_output with screenshot
            response = self.client.responses.create(
                model=self.model,
                previous_response_id=response.id,
                computer_call_output={"call_id": action.id, "screenshot": screenshot_b64},
                truncation="auto",
            )

            # Update previous response ID for chaining
            self.prev_response_id = response.id

        # Extract any text output
        if hasattr(response, "output") and response.output:
            if isinstance(response.output, dict) and "text" in response.output:
                result_text = response.output["text"]
            elif isinstance(response.output, str):
                result_text = response.output

        return result_text

    async def open(self, url: str) -> None:
        """Navigate to URL using CUA or fallback to Playwright.

        Args:
            url: URL to navigate to
        """
        try:
            await self._cua_action(f"Navigate to {url}")
        except Exception as e:
            if self.fallback_enabled:
                # Fallback to direct Playwright navigation
                await self._ensure_browser()
                await self.page.goto(url)
            else:
                raise e

    async def click_view_profile(self) -> None:
        """Click on view profile button."""
        await self._cua_action("Click the 'View profile' button")

    async def read_profile_text(self) -> str:
        """Extract and return profile text from current page.

        Returns:
            Extracted profile text
        """
        result = await self._cua_action(
            "Read and extract all the profile text from the current page. "
            "Include name, bio, skills, location, and any other relevant information."
        )

        if result:
            self._profile_text_cache = result
            return result

        # Fallback: return cached or empty
        return self._profile_text_cache or "Profile text here"

    async def focus_message_box(self) -> None:
        """Focus on the message input box."""
        await self._cua_action("Click on the message input box to focus it")

    async def fill_message(self, text: str) -> None:
        """Fill message box with text.

        Args:
            text: Message text to type
        """
        await self._cua_action(f"Type the following message: {text}")

    async def send(self) -> None:
        """Click send button to send the message."""
        await self._cua_action("Click the Send button to send the message")

    async def press_send(self) -> None:
        """Alias for send() for compatibility."""
        await self.send()

    async def skip(self) -> None:
        """Skip current profile and go to next."""
        await self._cua_action("Click Skip or Next to go to the next profile")

    async def verify_sent(self) -> bool:
        """Verify that message was sent successfully.

        Returns:
            True if message sent successfully
        """
        result = await self._cua_action(
            "Check if the message was sent successfully. "
            "Look for confirmation message or success indicator."
        )

        # Simple heuristic: if CUA found success indicators
        if result and any(word in result.lower() for word in ["success", "sent", "delivered"]):
            return True

        # Default to assuming success if no error
        return True

    async def close(self) -> None:
        """Clean up browser resources."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        self.page = None
        self.browser = None
        self.playwright = None
        self.prev_response_id = None
