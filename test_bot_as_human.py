#!/usr/bin/env python3
"""I AM THE HUMAN NOW - Testing the YC Matcher bot with full automation."""
import asyncio
import os
import time
from playwright.async_api import async_playwright

# Set environment for CUA login
os.environ["YC_EMAIL"] = os.getenv("YC_EMAIL", "")
os.environ["YC_PASSWORD"] = os.getenv("YC_PASSWORD", "")

async def test_full_bot_flow():
    """Act as human, fill the streamlit form, and run the bot."""
    print("🤖 BECOMING HUMAN - Testing YC Matcher Bot")
    print("=" * 50)
    
    async with async_playwright() as p:
        # Launch visible browser to see what's happening
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        print("📍 Navigating to Streamlit app...")
        await page.goto("http://localhost:8502")
        await page.wait_for_load_state("networkidle")
        
        print("⏳ Waiting for app to fully load...")
        await asyncio.sleep(3)
        
        # Fill in Your Profile
        print("📝 Filling in Your Profile...")
        profile_text = """Hey I'm Dr. Jung, a psychiatrist and builder. Currently shipping Brain Go Brrr: clinical-grade EEG analysis platform.

Stack: Python, PyTorch, FastAPI, React, Docker/K8s, AWS
Experience: MD from Ohio State, Psychiatry boards, pivoted to tech in 2024
Building: Open-source foundation model for EEGs (github.com/Clarity-Digital-Twin/brain-go-brrr)

Looking for: Full-stack technical cofounder ready to build and scale health-tech"""
        
        profile_textarea = await page.query_selector('textarea[aria-label="Your Profile"]')
        if not profile_textarea:
            profile_textarea = await page.query_selector('textarea:has-text("Describe yourself")')
        if not profile_textarea:
            profile_textarea = (await page.query_selector_all('textarea'))[0]
        
        await profile_textarea.fill(profile_text)
        print("✅ Profile filled")
        
        # Fill in Match Criteria
        print("🎯 Filling in Match Criteria...")
        criteria_text = """Strong YES if:
- Python + PyTorch/FastAPI expert
- Signal processing experience (EEG/time-series)
- Health-tech interest
- Ready within 3 months
- US-based, open to 50/50 equity

Strong NO if:
- Already full-time on own startup
- Wants upfront salary/contract
- Location requirement excluding NYC/remote"""
        
        criteria_textarea = await page.query_selector('textarea[aria-label="Match Criteria"]')
        if not criteria_textarea:
            criteria_textarea = (await page.query_selector_all('textarea'))[1]
        
        await criteria_textarea.fill(criteria_text)
        print("✅ Criteria filled")
        
        # Fill in Message Template
        print("💬 Filling in Message Template...")
        message_text = """Hey [Name],

Your [project/skill] caught my eye. I'm John, a psychiatrist shipping an open clinical AI prototype.

I need a technical cofounder to scale Brain Go Brrr into an enterprise platform. Quick call?

Calendly: calendly.com/jj-novamindnyc/30min
GitHub: github.com/Clarity-Digital-Twin/brain-go-brrr

Looking forward,
John"""
        
        message_textarea = await page.query_selector('textarea[aria-label="Message Template"]')
        if not message_textarea:
            message_textarea = (await page.query_selector_all('textarea'))[2]
        
        await message_textarea.fill(message_text)
        print("✅ Message template filled")
        
        # Set max profiles to 3 for testing
        print("🔢 Setting max profiles to 3...")
        max_profiles_input = await page.query_selector('input[type="number"]')
        if max_profiles_input:
            await max_profiles_input.fill("3")
        print("✅ Max profiles set to 3")
        
        # Check if CUA toggle is ON
        print("🔍 Checking CUA toggle status...")
        cua_status = await page.query_selector('text=/Engine: CUA/')
        if cua_status:
            print("✅ CUA is enabled!")
        else:
            print("⚠️ CUA might not be enabled, but continuing...")
        
        # Take screenshot before starting
        await page.screenshot(path="before_start.png")
        print("📸 Screenshot saved: before_start.png")
        
        # Click Start button
        print("🚀 CLICKING START AUTONOMOUS BROWSING...")
        start_button = await page.query_selector('button:has-text("Start Autonomous Browsing")')
        if not start_button:
            print("❌ Could not find Start button!")
            return
        
        await start_button.click()
        print("✅ Start button clicked!")
        
        # Wait a bit for processing to begin
        await asyncio.sleep(5)
        
        # Monitor for results or errors
        print("📊 Monitoring for results...")
        for i in range(30):  # Monitor for up to 150 seconds
            # Check for completion
            success = await page.query_selector('text=/Autonomous browsing complete/')
            error = await page.query_selector('text=/Failed to start/')
            
            if success:
                print("🎉 SUCCESS! Autonomous browsing completed!")
                
                # Get metrics
                metrics = await page.query_selector_all('.metric-container')
                if metrics:
                    print("📈 Results:")
                    for metric in metrics:
                        text = await metric.inner_text()
                        print(f"  • {text}")
                
                await page.screenshot(path="success_results.png")
                print("📸 Results screenshot: success_results.png")
                break
            
            if error:
                print("❌ Error occurred!")
                error_text = await page.query_selector('text=/Error Details/')
                if error_text:
                    details = await error_text.inner_text()
                    print(f"Error details: {details}")
                
                await page.screenshot(path="error_state.png")
                print("📸 Error screenshot: error_state.png")
                break
            
            print(f"⏳ Waiting... ({i*5}/150 seconds)")
            await asyncio.sleep(5)
        
        print("\n" + "=" * 50)
        print("🏁 Test complete!")
        
        # Keep browser open for 10 seconds to observe
        print("Browser will close in 10 seconds...")
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    print("🚀 GOD MODE ACTIVATED - FULL AUTONOMOUS TEST")
    print("This will:")
    print("1. Navigate to Streamlit")
    print("2. Fill all fields")  
    print("3. Start autonomous browsing")
    print("4. Monitor for results")
    print("\nStarting in 3 seconds...")
    time.sleep(3)
    
    asyncio.run(test_full_bot_flow())