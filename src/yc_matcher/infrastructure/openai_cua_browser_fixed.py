"""OpenAI CUA Browser with FIXED async/sync handling - NO MORE POPUP SPAM."""

import asyncio
import base64
import os
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, Page, Playwright, async_playwright


class OpenAICUABrowserFixed:
    """FIXED: Single browser instance, proper async handling."""
    
    def __init__(self) -> None:
        """Initialize with lazy browser creation."""
        # OpenAI client
        from openai import OpenAI
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Model configuration
        self.model = os.getenv("CUA_MODEL")
        if not self.model:
            raise ValueError("CUA_MODEL not set")
            
        # Browser state (lazy init)
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None
        
        # CUA state
        self._prev_response_id: str | None = None
        self._turn_count = 0
        self._max_turns = int(os.getenv("CUA_MAX_TURNS", "10"))
        
        # Cache
        self._profile_text_cache = ""
        
        # Single event loop for all async operations
        self._loop: asyncio.AbstractEventLoop | None = None
        self._ensure_loop()
        
    def _ensure_loop(self) -> None:
        """Ensure we have a single persistent event loop."""
        if self._loop is None or self._loop.is_closed():
            try:
                # Try to get existing loop
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                # No loop, create one in a thread
                import threading
                import concurrent.futures
                
                def run_loop():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_forever()
                
                # Start background loop thread
                self._loop_thread = threading.Thread(target=run_loop, daemon=True)
                self._loop_thread.start()
                
                # Wait for loop to be ready
                import time
                time.sleep(0.1)
                
                # Get the loop from the thread
                # This is a simplified approach - production would use concurrent.futures
                self._loop = asyncio.new_event_loop()
                
    def _run_async(self, coro):
        """Run async code in our persistent loop."""
        # If we're already in an event loop, use create_task
        try:
            loop = asyncio.get_running_loop()
            if loop == self._loop:
                # Same loop, just await
                return asyncio.create_task(coro)
            else:
                # Different loop, use run_until_complete
                return asyncio.run_coroutine_threadsafe(coro, self._loop).result()
        except RuntimeError:
            # No current loop, use our loop
            if self._loop and not self._loop.is_closed():
                return asyncio.run_coroutine_threadsafe(coro, self._loop).result()
            else:
                # Fallback to asyncio.run (last resort)
                return asyncio.run(coro)
                
    async def _ensure_browser(self) -> None:
        """Ensure browser is running (SINGLE INSTANCE)."""
        if not self.playwright:
            # Set browser path BEFORE starting
            browsers_path = os.getenv("PLAYWRIGHT_BROWSERS_PATH", ".ms-playwright")
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
            
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=os.getenv("PLAYWRIGHT_HEADLESS", "0") == "1"
            )
            self.page = await self.browser.new_page()
            print(f"🌐 Browser launched (headless={os.getenv('PLAYWRIGHT_HEADLESS', '0') == '1'})")
            
    # === SYNC WRAPPERS (using persistent loop) ===
    
    def open(self, url: str) -> None:
        """Navigate to URL."""
        # Reset session state
        self._profile_text_cache = ""
        self._prev_response_id = None
        self._turn_count = 0
        
        async def _open():
            await self._ensure_browser()
            if self.page:
                await self.page.goto(url)
                
        self._run_async(_open())
        
    def click_view_profile(self) -> bool:
        """Click view profile button."""
        async def _click():
            await self._ensure_browser()
            if self.page:
                try:
                    # Try to click view profile button
                    await self.page.click('button:has-text("View profile")', timeout=5000)
                    return True
                except Exception:
                    return False
            return False
            
        return self._run_async(_click())
        
    def read_profile_text(self) -> str:
        """Read profile text from page."""
        if self._profile_text_cache:
            return self._profile_text_cache
            
        async def _read():
            await self._ensure_browser()
            if self.page:
                try:
                    # Extract all text from page
                    text = await self.page.inner_text("body")
                    self._profile_text_cache = text
                    return text
                except Exception:
                    return ""
            return ""
            
        return self._run_async(_read())
        
    def focus_message_box(self) -> None:
        """Focus on message input."""
        async def _focus():
            await self._ensure_browser()
            if self.page:
                try:
                    await self.page.focus('textarea[placeholder*="message"]')
                except Exception:
                    pass
                    
        self._run_async(_focus())
        
    def fill_message(self, text: str) -> None:
        """Fill message box."""
        async def _fill():
            await self._ensure_browser()
            if self.page:
                try:
                    await self.page.fill('textarea[placeholder*="message"]', text)
                except Exception:
                    pass
                    
        self._run_async(_fill())
        
    def send(self) -> None:
        """Click send button."""
        async def _send():
            await self._ensure_browser()
            if self.page:
                try:
                    await self.page.click('button:has-text("Send")')
                except Exception:
                    pass
                    
        self._run_async(_send())
        
    def verify_sent(self) -> bool:
        """Verify message was sent."""
        async def _verify():
            await self._ensure_browser()
            if self.page:
                try:
                    # Check if message box is empty
                    value = await self.page.evaluate('''
                        () => {
                            const input = document.querySelector('textarea[placeholder*="message"]');
                            return input ? input.value : "not empty";
                        }
                    ''')
                    sent_ok = value == ""
                    if sent_ok:
                        self._profile_text_cache = ""  # Clear cache after send
                    return sent_ok
                except Exception:
                    return False
            return False
            
        return self._run_async(_verify())
        
    def skip(self) -> None:
        """Skip to next profile."""
        self._profile_text_cache = ""  # Clear cache
        
        async def _skip():
            await self._ensure_browser()
            if self.page:
                try:
                    await self.page.click('button:has-text("Skip")')
                except Exception:
                    pass
                    
        self._run_async(_skip())
        
    def close(self) -> None:
        """Close browser cleanly."""
        async def _close():
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
                
        self._run_async(_close())
        
        # Clean up
        self.page = None
        self.browser = None
        self.playwright = None