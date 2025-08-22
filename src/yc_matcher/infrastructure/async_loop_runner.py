"""Professional async loop runner - single thread, single browser, no spam."""

import asyncio
import atexit
import os
import threading
from collections.abc import Coroutine
from typing import Any, TypeVar

from playwright.async_api import Browser, Page, Playwright, async_playwright

T = TypeVar("T")


class AsyncLoopRunner:
    """Manages a single async event loop in a dedicated thread.

    This is THE solution to the browser spam problem:
    - ONE event loop that lives for the entire session
    - ONE Playwright instance
    - ONE browser instance
    - ONE page
    - All async operations run in this single loop
    - Sync methods submit work to this loop and wait for results

    No more asyncio.run() spam creating new loops/browsers!
    """

    def __init__(self) -> None:
        """Initialize the async loop runner."""
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None
        self._ready = threading.Event()
        self._stopping = False

        # CRITICAL: Don't start real browser in test mode
        if os.getenv("PYTEST_CURRENT_TEST"):
            print("⚠️ AsyncLoopRunner: Test mode detected, not starting browser")
            return  # Tests should mock this entirely
        
        # Start the event loop in a thread
        self._start_loop()

        # Register cleanup on exit
        atexit.register(self.cleanup)

    def _start_loop(self) -> None:
        """Start the event loop in a dedicated thread."""

        def run_loop() -> None:
            """Thread target - run event loop forever."""
            # Create new event loop for this thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            # Signal that loop is ready
            self._ready.set()

            # Run forever (until stop() is called)
            self._loop.run_forever()

            # Clean up after loop stops
            self._loop.close()

        # Start thread
        self._thread = threading.Thread(target=run_loop, daemon=True, name="AsyncLoopRunner")
        self._thread.start()

        # Wait for loop to be ready
        self._ready.wait(timeout=5)

        if not self._loop:
            raise RuntimeError("Failed to start async event loop")

    def submit(self, coro: Coroutine[Any, Any, T]) -> T:
        """Submit coroutine to event loop and wait for result.

        This is the KEY method that replaces asyncio.run().
        Instead of creating a new loop, we submit to the existing one.

        Args:
            coro: Async coroutine to run

        Returns:
            Result of the coroutine

        Raises:
            RuntimeError: If loop is not running
        """
        if not self._loop or not self._loop.is_running():
            raise RuntimeError("Event loop is not running")

        if self._stopping:
            raise RuntimeError("Runner is stopping")

        # Submit coroutine to the event loop thread
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)

        # Wait for result (blocks current thread)
        try:
            return future.result(timeout=30)  # 30 second timeout
        except Exception as e:
            # Re-raise exception from async context
            raise e

    async def ensure_browser(self) -> Page:
        """Ensure browser and page are initialized.

        This runs IN the event loop thread.
        Called lazily on first browser operation.

        Returns:
            The browser page (creates if needed)
        """
        # Only create if not exists
        if not self._playwright:
            import os

            # Set browser path before starting
            browsers_path = os.getenv("PLAYWRIGHT_BROWSERS_PATH", ".ms-playwright")
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path

            # Start playwright
            self._playwright = await async_playwright().start()

        # Only launch browser if not exists or disconnected
        if not self._browser or not self._browser.is_connected():
            import os

            # Launch browser (headless based on env)
            self._browser = await self._playwright.chromium.launch(
                headless=os.getenv("PLAYWRIGHT_HEADLESS", "0") == "1",
                args=["--no-sandbox", "--disable-setuid-sandbox"] if os.getenv("CI") else [],
            )

            print(
                f"🌐 Browser launched (single instance, headless={os.getenv('PLAYWRIGHT_HEADLESS', '0') == '1'})"
            )

        # Only create page if not exists
        if not self._page or self._page.is_closed():
            self._page = await self._browser.new_page()

        return self._page

    async def close_browser(self) -> None:
        """Close browser and playwright.

        This runs IN the event loop thread.
        """
        if self._page and not self._page.is_closed():
            await self._page.close()
            self._page = None

        if self._browser and self._browser.is_connected():
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        print("🛑 Browser closed")

    def cleanup(self) -> None:
        """Clean up resources (called on exit)."""
        if self._stopping:
            return  # Already cleaning up

        self._stopping = True

        if self._loop and self._loop.is_running():
            # Schedule browser cleanup in the loop
            try:
                future = asyncio.run_coroutine_threadsafe(self.close_browser(), self._loop)
                future.result(timeout=5)
            except Exception:
                pass  # Best effort

            # Stop the event loop
            self._loop.call_soon_threadsafe(self._loop.stop)

        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

        print("✅ AsyncLoopRunner cleaned up")
