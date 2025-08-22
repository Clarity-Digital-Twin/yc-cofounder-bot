#!/usr/bin/env python
"""Test that browser opens VISIBLY for login."""

import asyncio
import os

from playwright.async_api import async_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = ".ms-playwright"
os.environ["PLAYWRIGHT_HEADLESS"] = "0"  # VISIBLE!


async def test_visible_browser():
    """Test visible browser for YC login flow."""
    async with async_playwright() as p:
        print("🌐 Testing VISIBLE browser launch...")

        # Test 1: Open Streamlit and trigger browser
        ui_browser = await p.chromium.launch(headless=True)  # UI can be headless
        ui_page = await ui_browser.new_page()

        print("📱 Opening Streamlit UI...")
        await ui_page.goto("http://localhost:8504")
        await ui_page.wait_for_timeout(2000)

        # Fill form quickly
        await ui_page.locator("textarea").first.fill("Test profile")
        await ui_page.locator("textarea").nth(1).fill("Test criteria")
        await ui_page.locator("textarea").nth(2).fill("Hi {name}!")

        print("🚀 Clicking Start button...")
        # Look for the actual button text
        start_btn = ui_page.locator('button:has-text("Start Autonomous Browsing")')
        if await start_btn.count() > 0:
            await start_btn.click()
        else:
            print("❌ Start button not found!")

        print("\n⚠️  A VISIBLE browser window should open now!")
        print("    This is where user would log into YC")
        print("    Waiting 10 seconds to observe...")

        await ui_page.wait_for_timeout(10000)

        # Check for any status
        status = ui_page.locator(".stAlert")
        if await status.count() > 0:
            texts = await status.all_inner_texts()
            for text in texts[:3]:  # First 3 messages
                print(f"    Status: {text[:100]}")

        await ui_browser.close()
        print("\n✅ Test complete!")
        print("Did you see a browser window open? That's where login happens!")


if __name__ == "__main__":
    asyncio.run(test_visible_browser())
