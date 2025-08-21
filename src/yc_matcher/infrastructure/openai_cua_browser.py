"""OpenAI Computer Use adapter using Responses API with Playwright executor.

Following clean code principles:
- Single Responsibility: CUA plans, Playwright executes
- Dependency Inversion: Implements ComputerUsePort interface
- Open/Closed: Extensible via port, not modification
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

from openai import OpenAI
from playwright.async_api import Browser, Page, Playwright, async_playwright


class OpenAICUABrowser:
    """Browser automation using OpenAI CUA (Responses API) + Playwright.

    Architecture:
    - CUA (via Responses API) = Planner/Analyzer
    - Playwright = Executor/Browser Control
    - Loop: Screenshot → CUA analyze → CUA suggest → Playwright execute

    This implements the correct Responses API pattern per the official spec.
    """

    def __init__(self) -> None:
        """Initialize CUA browser with Responses API client and Playwright."""
        # OpenAI client for Responses API
        self.client: Any = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

        # Logger for events (will be injected via DI in production)
        self.logger = None

        # HIL approval callback (will be set by UI)
        self.hil_approve_callback = None

        # Screenshot callback for UI display
        self.screenshot_callback = None

    async def _ensure_browser(self) -> None:
        """Ensure Playwright browser is running (lazy initialization)."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=os.getenv("PLAYWRIGHT_HEADLESS", "0") == "1"
            )
            self.page = await self.browser.new_page()

    def _should_stop(self) -> bool:
        """Check if STOP flag exists."""
        stop_file = Path(".runs/stop.flag")
        return stop_file.exists()

    def _log_event(self, event: dict[str, Any]) -> None:
        """Log event to logger if available."""
        if self.logger:
            self.logger.log_event(event.get("event", "unknown"), event)

    async def _hil_acknowledge(self, safety_check: Any) -> bool:
        """Get HIL acknowledgment for safety check."""
        if self.hil_approve_callback:
            return await self.hil_approve_callback(safety_check)
        # Default: conservative, don't proceed without explicit approval
        return False

    async def _execute_action(self, action: Any) -> None:
        """Execute CUA-suggested action via Playwright.

        Args:
            action: Computer call action from CUA with type and parameters
        """
        await self._ensure_browser()
        assert self.page is not None  # Type narrowing for mypy

        action_type = getattr(action, "type", "")

        if action_type == "click":
            # Click at coordinates
            coords = getattr(action, "coordinates", {})
            if coords:
                # Playwright expects selector or coordinates
                await self.page.mouse.click(coords.get("x", 0), coords.get("y", 0))

        elif action_type == "type":
            # Type text
            text = getattr(action, "text", "")
            if text:
                await self.page.keyboard.type(text)

        elif action_type == "scroll":
            # Scroll page
            delta = getattr(action, "delta", 100)
            await self.page.mouse.wheel(0, delta)

        elif action_type == "key":
            # Press key
            key = getattr(action, "key", "")
            if key:
                await self.page.keyboard.press(key)

        elif action_type == "wait":
            # Wait for a moment
            import asyncio

            await asyncio.sleep(1)

        elif action_type == "screenshot":
            # Just take screenshot, no action needed
            pass

    async def _cua_action(self, instruction: str) -> str | None:
        """Core CUA loop: plan with Responses API, execute with Playwright.

        This implements the correct API specification:
        1. Send request with proper input structure
        2. Parse output array for computer_call items
        3. Execute actions and send computer_call_output
        4. Handle safety checks with HIL
        5. Check STOP flag in loop

        Args:
            instruction: What to do (e.g., "Click the first profile")

        Returns:
            Text output from CUA if any
        """
        await self._ensure_browser()
        assert self.page is not None  # Type narrowing for mypy

        # Build input content
        input_content = [{"type": "input_text", "text": instruction}]

        # Only include screenshot if we have navigated somewhere
        current_url = await self.page.evaluate("() => window.location.href")
        if current_url and current_url != "about:blank":
            screenshot = await self.page.screenshot()
            screenshot_b64 = base64.b64encode(screenshot).decode()
            input_content.append(
                {"type": "input_image", "image_url": f"data:image/png;base64,{screenshot_b64}"}
            )

        # 1) First turn (plan)
        response = self.client.responses.create(
            model=self.model,
            tools=[
                {
                    "type": "computer_use_preview",
                    "display_width": 1920,
                    "display_height": 1080,
                    "environment": "browser",
                }
            ],
            input=[{"role": "user", "content": input_content}],
            truncation="auto",
            previous_response_id=self.prev_response_id,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        self.prev_response_id = response.id

        # 2) Loop until no computer_call items (with turn cap for safety)
        MAX_TURNS = int(os.getenv("CUA_MAX_TURNS", "40"))
        turns = 0

        while turns < MAX_TURNS:
            # STOP gate (bail immediately and log)
            if self._should_stop():
                self._log_event({"event": "stopped", "where": "_cua_action", "reason": "stop_flag"})
                break

            # Parse output list items; find the first computer_call
            output_items = getattr(response, "output", []) or []
            calls = [item for item in output_items if getattr(item, "type", "") == "computer_call"]

            if not calls:
                break  # No more computer calls

            turns += 1
            if turns >= MAX_TURNS:
                self._log_event({"event": "max_turns_reached", "turns": turns})
                break

            call = calls[0]
            call_id = getattr(call, "call_id", None) or getattr(call, "id", None)
            action = getattr(call, "action", None)

            if not action:
                break

            # Execute action locally
            await self._execute_action(action)

            # New screenshot after action
            screenshot = await self.page.screenshot()
            screenshot_b64 = base64.b64encode(screenshot).decode()

            # Store screenshot for UI display if callback set
            if self.screenshot_callback:
                self.screenshot_callback(screenshot_b64)

            # Handle safety checks if present (default to reject for safety)
            acknowledged: list[dict[str, Any]] = []
            pending_checks = getattr(call, "pending_safety_checks", []) or []
            for safety_check in pending_checks:
                # Only acknowledge if HIL callback is set AND approves
                if self.hil_approve_callback and await self._hil_acknowledge(safety_check):
                    acknowledged.append(
                        {
                            "id": getattr(safety_check, "id", ""),
                            "code": getattr(safety_check, "code", ""),
                            "message": getattr(safety_check, "message", ""),
                        }
                    )
                else:
                    # Default to reject for safety
                    self._log_event(
                        {
                            "event": "stopped",
                            "reason": "safety_check_not_acknowledged",
                            "safety_check": str(safety_check),
                            "has_callback": bool(self.hil_approve_callback),
                        }
                    )
                    return None

            # Get current URL for better context
            current_url = await self.page.evaluate("() => window.location.href")

            # Respond with computer_call_output
            response = self.client.responses.create(
                model=self.model,
                previous_response_id=self.prev_response_id,
                tools=[
                    {
                        "type": "computer_use_preview",
                        "display_width": 1920,
                        "display_height": 1080,
                        "environment": "browser",
                    }
                ],
                input=[
                    {
                        "type": "computer_call_output",
                        "call_id": call_id,
                        "output": {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{screenshot_b64}",
                        },
                        "acknowledged_safety_checks": acknowledged,
                        "current_url": current_url,
                    }
                ],
                truncation="auto",
            )
            self.prev_response_id = response.id

        # 3) Extract any text output (robust parsing)
        text_output = None
        output_items = getattr(response, "output", []) or []
        for item in output_items:
            if getattr(item, "type", "") == "output_text":
                text_output = getattr(item, "text", None)
                break

        return text_output

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
                assert self.page is not None  # Type narrowing
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
        return self._profile_text_cache or ""

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

        More strict verification:
        - Asks CUA for explicit true/false answer
        - No default True assumption
        - Could add Playwright DOM fallback

        Returns:
            True only if message confirmed sent
        """
        # Ask CUA for explicit confirmation
        result = await self._cua_action(
            "Reply strictly 'true' or 'false': has the message been sent successfully? "
            "Look for a confirmation toast, banner, or an emptied message box."
        )

        # Only return True for explicit positive confirmation
        if result and result.strip().lower() in {"true", "yes"}:
            return True

        # Optional: Playwright DOM heuristic as fallback
        if self.page:
            try:
                # Example: Check if message input is empty (was cleared after send)
                # This is site-specific and should be customized
                message_box_empty = await self.page.evaluate("""
                    () => {
                        const input = document.querySelector('textarea[placeholder*="message"]');
                        return input ? input.value === '' : false;
                    }
                """)
                if message_box_empty:
                    return True
            except Exception:
                pass  # Fallback failed, continue

        # Conservative: return False if uncertain
        # Emit error event for observability
        self._log_event({
            "event": "error",
            "type": "verify_sent_failed",
            "reason": "could_not_confirm_sent",
            "cua_result": result if result else None,
            "message": "Message send could not be verified"
        })
        return False

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
