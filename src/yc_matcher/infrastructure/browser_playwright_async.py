"""Async-compatible Playwright browser that works with AsyncLoopRunner."""

from __future__ import annotations

import os
from collections.abc import Iterable
from typing import Any

from playwright.async_api import Page

from .async_loop_runner import AsyncLoopRunner

# SINGLETON: Share one AsyncLoopRunner across ALL browser instances
_shared_runner: AsyncLoopRunner | None = None


def _get_shared_runner() -> AsyncLoopRunner:
    """Get or create the shared AsyncLoopRunner singleton."""
    global _shared_runner
    if _shared_runner is None:
        _shared_runner = AsyncLoopRunner()
    return _shared_runner


class PlaywrightBrowserAsync:
    """Async Playwright adapter using AsyncLoopRunner for proper async/sync bridging.
    
    This solves the "Playwright Sync API inside asyncio loop" error by:
    1. Using async Playwright API internally
    2. Running all operations through AsyncLoopRunner
    3. Providing sync methods that submit async work to the runner
    4. SINGLETON: All instances share the same browser via shared AsyncLoopRunner
    """

    def __init__(self) -> None:
        """Initialize with SHARED AsyncLoopRunner (singleton pattern)."""
        # Use the shared runner - ensures single browser instance
        self._runner = _get_shared_runner()
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
            
            # Auto-login if credentials are provided and we're on YC
            if "startupschool.org" in url:
                await self._auto_login_if_needed(page)
        
        self._runner.submit(_open())
    
    async def _auto_login_if_needed(self, page: Page) -> None:
        """Automatically log in to YC if credentials are provided."""
        import os
        
        email = os.getenv("YC_EMAIL")
        password = os.getenv("YC_PASSWORD")
        
        if not email or not password:
            return  # No credentials, skip auto-login
        
        # Check if already logged in
        await page.wait_for_load_state("networkidle", timeout=5000)
        
        # Look for login form elements
        try:
            # Check if we're already logged in
            if await page.locator('button:has-text("View profile")').count() > 0:
                print("✅ Already logged in to YC")
                return
            
            # Look for sign in link/button
            sign_in = page.locator('a:has-text("Sign in"), button:has-text("Sign in"), a:has-text("Log in"), button:has-text("Log in")')
            if await sign_in.count() > 0:
                print("🔐 Clicking sign in button...")
                await sign_in.first.click()
                await page.wait_for_load_state("networkidle", timeout=5000)
            
            # Wait a bit after clicking sign in
            await page.wait_for_timeout(1000)
            
            # Fill username/email field - look for VISIBLE text input
            email_input = page.locator('input[type="text"]:visible, input[type="email"]:visible').first
            if await email_input.count() > 0:
                print(f"📧 Entering email: {email}")
                await email_input.fill(email)
                await page.wait_for_timeout(500)  # Small delay
            
            # Fill password field
            password_input = page.locator('input[type="password"]:visible').first
            if await password_input.count() > 0:
                print("🔑 Entering password...")
                await password_input.fill(password)
                await page.wait_for_timeout(500)  # Small delay
            
            # Submit the form - look for the Log In button
            submit_btn = page.locator('button:has-text("Log In"):visible, button:has-text("Log in"):visible, button[type="submit"]:visible').first
            if await submit_btn.count() > 0:
                print("🚀 Submitting login form...")
                await submit_btn.click()
                
                # Wait for navigation after login
                try:
                    await page.wait_for_url("**/cofounder-matching**", timeout=10000)
                except:
                    # Fallback - just wait for page to settle
                    await page.wait_for_load_state("networkidle", timeout=10000)
                
                # Navigate to cofounder matching if we're not there
                if "cofounder-matching" not in page.url:
                    await page.goto("https://www.startupschool.org/cofounder-matching")
                    await page.wait_for_load_state("networkidle", timeout=5000)
                
                print("✅ Logged in successfully")
                
        except Exception as e:
            print(f"⚠️ Auto-login failed: {e}")
            print("Please log in manually")

    def is_logged_in(self) -> bool:
        """Check if user is logged into YC."""
        async def _check() -> bool:
            page = await self._ensure_page_async()
            
            # Wait a bit for page to settle
            await page.wait_for_load_state("networkidle", timeout=3000)
            
            # Check for various logged-in indicators
            selectors = [
                'button:has-text("View profile")',
                'button:has-text("Skip")',
                '.profile-card',
                '[data-test="profile"]',
                'a:has-text("Sign out")',
                'a:has-text("Log out")',
                'button:has-text("Message")',
            ]
            
            for selector in selectors:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        return True
                except:
                    pass
            
            # Also check we're NOT on login page
            if "login" in page.url.lower() or "signin" in page.url.lower():
                return False
            
            # Check for absence of login buttons
            login_count = await page.locator('a:has-text("Sign in"), button:has-text("Sign in")').count()
            return login_count == 0
        
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