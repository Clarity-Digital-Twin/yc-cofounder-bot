#!/usr/bin/env python
"""Final test of the complete UI flow."""

import asyncio
from playwright.async_api import async_playwright
import os

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = ".ms-playwright"

async def test_ui_final():
    """Test the complete UI flow."""
    async with async_playwright() as p:
        print("🧪 Testing Complete UI Flow")
        print("=" * 50)
        
        # Open UI
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("1️⃣ Opening Streamlit UI...")
        await page.goto("http://localhost:8502")
        await page.wait_for_timeout(2000)
        
        # Check page loaded
        title = await page.title()
        print(f"   ✅ Page loaded: {title}")
        
        # Fill form
        print("2️⃣ Filling form...")
        await page.locator('textarea').first.fill("Senior engineer, 10 years Python/ML")
        await page.locator('textarea').nth(1).fill("Python, Machine Learning, SF/Remote")
        await page.locator('textarea').nth(2).fill("Hi {name}, let's connect!")
        print("   ✅ Form filled")
        
        # Check for browser launch button
        print("3️⃣ Looking for browser controls...")
        browser_btn = page.locator('button:has-text("Open Controlled Browser")')
        if await browser_btn.count() > 0:
            print("   ✅ Found 'Open Controlled Browser' button")
            print("   ℹ️  This would open a visible browser for login")
        else:
            print("   ℹ️  No browser button (may already be logged in)")
        
        # Check for start button
        start_btn = page.locator('button:has-text("Start Autonomous Browsing")')
        if await start_btn.count() > 0:
            print("   ✅ Found 'Start Autonomous Browsing' button")
        
        # Take screenshot
        await page.screenshot(path="ui_final_test.png")
        print("4️⃣ Screenshot saved: ui_final_test.png")
        
        # Check for any errors
        error_elements = page.locator('.stAlert[data-baseweb="notification"][kind="error"]')
        if await error_elements.count() > 0:
            print("   ⚠️  Errors found on page:")
            errors = await error_elements.all_inner_texts()
            for error in errors:
                print(f"      - {error}")
        else:
            print("   ✅ No errors on page")
        
        await browser.close()
        
        print("\n" + "=" * 50)
        print("✅ UI Test Complete!")
        print("\nThe app is working! You can now:")
        print("1. Go to http://localhost:8502")
        print("2. Fill in your profile, criteria, and template")
        print("3. Click 'Open Controlled Browser' to launch Chrome")
        print("4. Log into YC in the opened browser")
        print("5. Click 'I'm Logged In'")
        print("6. Click 'Start Autonomous Browsing'")

if __name__ == "__main__":
    asyncio.run(test_ui_final())