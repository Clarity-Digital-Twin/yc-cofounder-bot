#!/usr/bin/env python
"""Monitor the automation in real-time."""

import asyncio
import os

from playwright.async_api import async_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = ".ms-playwright"

async def monitor_automation():
    """Monitor the automation as it runs."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # VISIBLE browser
        page = await browser.new_page()

        print("🌐 Opening Streamlit app...")
        await page.goto("http://localhost:8504")
        await page.wait_for_timeout(2000)

        # Quick fill
        print("📝 Quick filling form...")
        await page.locator('textarea').first.fill("Python developer, 10 years experience")
        await page.locator('textarea').nth(1).fill("Python, AI, ML")
        await page.locator('textarea').nth(2).fill("Hi {name}, interested in connecting!")

        # Start
        print("🚀 Starting...")
        start_btn = page.locator('button').filter(has_text="Start")
        await start_btn.first.click()

        # Monitor for 30 seconds
        print("\n📊 Monitoring for 30 seconds...")
        print("Watch for:")
        print("  - Progress messages")
        print("  - Browser windows opening")
        print("  - Status updates")

        for i in range(30):
            await page.wait_for_timeout(1000)

            # Check for status updates
            status = page.locator('.stAlert')
            if await status.count() > 0:
                texts = await status.all_inner_texts()
                for text in texts:
                    if text and len(text) < 200:
                        print(f"  Status: {text}")

            # Check for progress
            if i % 5 == 0:
                print(f"  [{i}s] Checking...")

        await page.screenshot(path="monitor_final.png")
        print("\n📸 Final screenshot saved")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(monitor_automation())
