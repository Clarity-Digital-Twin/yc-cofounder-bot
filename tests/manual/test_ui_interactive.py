#!/usr/bin/env python
"""Interactive Playwright test of Streamlit UI."""

import asyncio
from playwright.async_api import async_playwright
import os

# Set browser path
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = ".ms-playwright"

async def test_ui():
    """Test the Streamlit UI interactively."""
    async with async_playwright() as p:
        # Launch browser (visible for debugging)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🌐 Opening Streamlit app...")
        await page.goto("http://localhost:8504")
        
        # Wait for app to load
        await page.wait_for_timeout(2000)
        
        # Take screenshot
        await page.screenshot(path="streamlit_ui.png")
        print("📸 Screenshot saved to streamlit_ui.png")
        
        # Fill in the three inputs
        print("📝 Filling in form fields...")
        
        # Find and fill "Your Profile" textarea
        profile_input = page.locator('textarea').first
        await profile_input.fill("I'm a technical founder with 10 years in ML/AI")
        
        # Find and fill "Match Criteria" 
        criteria_input = page.locator('textarea').nth(1)
        await criteria_input.fill("Python, Machine Learning, San Francisco")
        
        # Find and fill "Message Template"
        template_input = page.locator('textarea').nth(2)
        await template_input.fill("Hi {name}, I noticed your experience in {skill}. Would love to connect!")
        
        await page.wait_for_timeout(1000)
        
        # Take screenshot after filling
        await page.screenshot(path="streamlit_filled.png")
        print("📸 Filled form screenshot saved")
        
        # Look for the Start button
        start_button = page.locator('button:has-text("Start")')
        if await start_button.count() > 0:
            print("✅ Found Start button!")
            await start_button.click()
            print("🚀 Clicked Start button")
            
            # Wait for processing
            await page.wait_for_timeout(5000)
            
            # Take final screenshot
            await page.screenshot(path="streamlit_running.png")
            print("📸 Running state screenshot saved")
        else:
            print("❌ Start button not found")
        
        # Keep browser open for inspection
        print("\n⏸️  Browser will stay open for 10 seconds for inspection...")
        await page.wait_for_timeout(10000)
        
        await browser.close()
        print("✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_ui())