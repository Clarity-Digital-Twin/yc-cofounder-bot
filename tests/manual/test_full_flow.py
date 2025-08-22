#!/usr/bin/env python
"""Test full flow: Fill form → Start → Verify browser automation."""

import asyncio
from playwright.async_api import async_playwright
import os
import time

# Set browser path
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = ".ms-playwright"

async def test_full_flow():
    """Test complete flow including browser automation."""
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🌐 Opening Streamlit app...")
        await page.goto("http://localhost:8504")
        await page.wait_for_timeout(3000)
        
        # Fill in the form
        print("📝 Filling in form fields...")
        
        # Fill profile
        await page.locator('textarea').first.fill(
            "Technical founder, 10+ years Python/ML experience, "
            "built 3 startups, looking for technical co-founder"
        )
        
        # Fill criteria
        await page.locator('textarea').nth(1).fill(
            "Python, Machine Learning, FastAPI, startup experience, "
            "San Francisco or remote"
        )
        
        # Fill template  
        await page.locator('textarea').nth(2).fill(
            "Hi {name}, your experience with {skill} caught my attention. "
            "I'm building an AI startup and looking for a technical co-founder. "
            "Would love to connect!"
        )
        
        # Adjust threshold slider if present
        sliders = page.locator('input[type="range"]')
        if await sliders.count() > 0:
            print("📊 Adjusting threshold...")
            # Set auto-send threshold to 0.5 (middle)
            await sliders.first.fill("0.5")
        
        # Take pre-start screenshot
        await page.screenshot(path="test_before_start.png")
        
        # Click Start button
        start_button = page.locator('button:has-text("Start Autonomous Browsing")')
        if await start_button.count() == 0:
            start_button = page.locator('button:has-text("Start")')
        
        if await start_button.count() > 0:
            print("🚀 Starting autonomous browsing...")
            await start_button.click()
            
            # Wait for processing to begin
            await page.wait_for_timeout(5000)
            
            # Check for any error messages
            error_expander = page.locator('details:has-text("Error Details")')
            if await error_expander.count() > 0:
                print("❌ Error found - expanding details...")
                await error_expander.click()
                error_text = await page.locator('pre').inner_text()
                print(f"Error: {error_text[:500]}")
                
                # Check if it's the browser not found error
                if "Executable doesn't exist" in error_text:
                    print("\n🔧 Browser executable issue detected")
                    print("Checking PLAYWRIGHT_BROWSERS_PATH...")
                    
            else:
                print("✅ No errors - automation running!")
                
                # Look for progress indicators
                progress = page.locator('text=/Processing profile/')
                if await progress.count() > 0:
                    print("📊 Found progress indicator")
                    
                # Check for results
                await page.wait_for_timeout(10000)
                
                results = page.locator('text=/Evaluated/')
                if await results.count() > 0:
                    result_text = await results.inner_text()
                    print(f"📈 Results: {result_text}")
            
            # Final screenshot
            await page.screenshot(path="test_after_start.png")
            print("📸 Final screenshot saved")
            
        else:
            print("❌ Start button not found!")
            # Debug: print all buttons
            buttons = await page.locator('button').all_inner_texts()
            print(f"Available buttons: {buttons}")
        
        await browser.close()
        print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_full_flow())