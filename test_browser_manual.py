#!/usr/bin/env python
"""Manual test to verify browser functionality."""

import asyncio
from playwright.async_api import async_playwright

async def test_browser():
    """Test if Playwright can open a browser."""
    print("🧪 Testing Playwright browser...")
    
    async with async_playwright() as p:
        print("✅ Playwright initialized")
        
        # Launch browser (headless for WSL)
        browser = await p.chromium.launch(headless=True)
        print("✅ Browser launched")
        
        # Create page
        page = await browser.new_page()
        print("✅ Page created")
        
        # Navigate to Google (simple test)
        await page.goto("https://www.google.com")
        print("✅ Navigated to Google")
        
        # Get title
        title = await page.title()
        print(f"✅ Page title: {title}")
        
        # Take screenshot
        await page.screenshot(path="test_screenshot.png")
        print("✅ Screenshot saved to test_screenshot.png")
        
        # Close
        await browser.close()
        print("✅ Browser closed")
        
    print("🎉 Browser test complete!")

if __name__ == "__main__":
    asyncio.run(test_browser())