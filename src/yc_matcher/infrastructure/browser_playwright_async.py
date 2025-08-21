"""Async-compatible Playwright browser that works with AsyncLoopRunner."""

from __future__ import annotations

import os
from collections.abc import Iterable
from typing import Any

from playwright.async_api import Page

from .async_loop_runner import AsyncLoopRunner


class PlaywrightBrowserAsync:
    """Async Playwright adapter using AsyncLoopRunner for proper async/sync bridging.
    
    This solves the "Playwright Sync API inside asyncio loop" error by:
    1. Using async Playwright API internally
    2. Running all operations through AsyncLoopRunner
    3. Providing sync methods that submit async work to the runner
    """

    def __init__(self) -> None:
        """Initialize with AsyncLoopRunner."""
        self._runner = AsyncLoopRunner()
        self._page: Page | None = None

    async def _ensure_page_async(self) -> Page:
        """Ensure browser page exists (async version)."""
        if self._page is not None:
            return self._page
            
        # Get or create the page via runner
        self._page = await self._runner.ensure_browser()
        return self._page

    def _ensure_page(self) -> Page:
        """Ensure browser page exists (sync wrapper)."""
        return self._runner.submit(self._ensure_page_async())

    def open(self, url: str) -> None:
        """Open URL in browser (sync method)."""
        async def _open() -> None:
            page = await self._ensure_page_async()
            await page.goto(url)
        
        self._runner.submit(_open())

    def is_logged_in(self) -> bool:
        """Check if user is logged into YC."""
        async def _check() -> bool:
            page = await self._ensure_page_async()
            # Check for elements that only appear when logged in
            view_profile_count = await page.locator('button:has-text("View profile")').count()
            profile_card_count = await page.locator('.profile-card').count()
            profile_data_count = await page.locator('[data-test="profile"]').count()
            
            return (view_profile_count > 0 or 
                   profile_card_count > 0 or 
                   profile_data_count > 0)
        
        return self._runner.submit(_check())

    def click_view_profile(self) -> bool:
        """Click View Profile button."""
        async def _click() -> bool:
            page = await self._ensure_page_async()
            labels = ["View profile", "View Profile", "VIEW PROFILE"]
            
            for label in labels:
                try:
                    btn = page.get_by_role("button", name=label)
                    if await btn.count() > 0:
                        await btn.first.click()
                        return True
                except Exception:
                    pass
                    
                try:
                    link = page.get_by_role("link", name=label)
                    if await link.count() > 0:
                        await link.first.click()
                        return True
                except Exception:
                    pass
            
            return False
        
        return self._runner.submit(_click())

    def read_profile_text(self) -> str:
        """Read profile text from page."""
        async def _read() -> str:
            page = await self._ensure_page_async()
            await page.wait_for_load_state("networkidle", timeout=5000)
            
            # Try multiple selectors
            selectors = [
                "main", ".profile-content", "#profile", 
                "[role='main']", ".container", "article"
            ]
            
            for selector in selectors:
                try:
                    elem = page.locator(selector).first
                    if await elem.count() > 0:
                        text = await elem.inner_text()
                        if text and len(text) > 100:
                            return text
                except Exception:
                    continue
            
            # Fallback to body text
            return await page.locator("body").inner_text()
        
        return self._runner.submit(_read())

    def skip(self) -> None:
        """Skip current profile."""
        async def _skip() -> None:
            page = await self._ensure_page_async()
            labels = ["Skip", "SKIP", "Next", "NEXT", "Pass", "PASS"]
            
            for label in labels:
                try:
                    btn = page.get_by_role("button", name=label)
                    if await btn.count() > 0:
                        await btn.first.click()
                        return
                except Exception:
                    pass
        
        self._runner.submit(_skip())

    def focus_message_box(self) -> None:
        """Focus the message input box."""
        async def _focus() -> None:
            page = await self._ensure_page_async()
            selectors = [
                "textarea[placeholder*='message']",
                "textarea[placeholder*='Message']", 
                "input[type='text'][placeholder*='message']",
                "#message", "[name='message']"
            ]
            
            for selector in selectors:
                try:
                    elem = page.locator(selector).first
                    if await elem.count() > 0:
                        await elem.focus()
                        return
                except Exception:
                    pass
        
        self._runner.submit(_focus())

    def fill_message(self, text: str) -> None:
        """Fill message in the input box."""
        async def _fill() -> None:
            page = await self._ensure_page_async()
            selectors = [
                "textarea[placeholder*='message']",
                "textarea[placeholder*='Message']",
                "input[type='text'][placeholder*='message']", 
                "#message", "[name='message']"
            ]
            
            for selector in selectors:
                try:
                    elem = page.locator(selector).first
                    if await elem.count() > 0:
                        await elem.fill(text)
                        return
                except Exception:
                    pass
        
        self._runner.submit(_fill())

    def send(self) -> None:
        """Send the message."""
        async def _send() -> None:
            page = await self._ensure_page_async()
            labels = ["Send", "SEND", "Send message", "Send Message", "Submit"]
            
            for label in labels:
                try:
                    btn = page.get_by_role("button", name=label)
                    if await btn.count() > 0:
                        await btn.first.click()
                        return
                except Exception:
                    pass
        
        self._runner.submit(_send())

    def verify_sent(self) -> bool:
        """Verify message was sent."""
        async def _verify() -> bool:
            page = await self._ensure_page_async()
            # Look for success indicators
            success_patterns = [
                "Message sent", "Successfully sent", "Sent!", 
                "Your message has been sent", "✓", "✅"
            ]
            
            page_text = await page.locator("body").inner_text()
            page_text_lower = page_text.lower()
            
            for pattern in success_patterns:
                if pattern.lower() in page_text_lower:
                    return True
            
            return False
        
        return self._runner.submit(_verify())

    def cleanup(self) -> None:
        """Clean up browser resources."""
        if self._runner:
            self._runner.cleanup()