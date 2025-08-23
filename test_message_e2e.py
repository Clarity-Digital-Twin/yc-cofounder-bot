#!/usr/bin/env python3
"""
End-to-end test to reproduce the message sending issue.
Run this with a real browser to see what's happening.
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

# Set test environment
os.environ["PLAYWRIGHT_HEADLESS"] = "0"  # Show browser
os.environ["PACE_MIN_SECONDS"] = "0"     # No delays

async def test_message_flow():
    """Test the complete message flow with visual browser"""
    
    print("\n" + "="*60)
    print("E2E MESSAGE FLOW TEST")
    print("="*60)
    
    # 1. Test with Playwright adapter (visible browser)
    print("\n🔧 Testing with Playwright Browser Adapter...")
    from yc_matcher.infrastructure.browser_playwright_async import BrowserAdapterPlaywrightAsync
    from yc_matcher.infrastructure.jsonl_logger import JSONLLogger
    
    browser = BrowserAdapterPlaywrightAsync()
    logger = JSONLLogger(".runs/e2e_test.jsonl")
    browser.logger = logger
    
    try:
        # Navigate to a test page with a textarea
        print("1. Opening test page...")
        # Use a simple page with textarea for testing
        test_url = "data:text/html,<html><body><h1>Test Page</h1><textarea id='message' placeholder='Type message here'></textarea><button id='send'>Send</button></body></html>"
        success = browser.open(test_url)
        print(f"   Navigation: {'✅' if success else '❌'}")
        
        if not success:
            print("   ❌ Failed to navigate")
            return
            
        # Wait for user to see the page
        print("\n2. Page loaded. You should see a textarea and button.")
        await asyncio.sleep(2)
        
        # Try to fill message
        test_message = "This is a test message from the E2E test!"
        print(f"\n3. Attempting to fill message: '{test_message}'")
        
        try:
            browser.fill_message(test_message)
            print("   ✅ fill_message() called successfully")
        except Exception as e:
            print(f"   ❌ fill_message() failed: {e}")
            import traceback
            traceback.print_exc()
            
        # Wait to see if message appears
        print("\n4. Waiting 3 seconds to see if message appears in textarea...")
        await asyncio.sleep(3)
        
        # Check if message is visible
        print("\n5. Checking DOM for message...")
        try:
            # Direct check using Playwright
            if hasattr(browser, '_page') and browser._page:
                textarea_value = await browser._page.evaluate("""
                    () => {
                        const textarea = document.querySelector('textarea');
                        return textarea ? textarea.value : null;
                    }
                """)
                
                if textarea_value == test_message:
                    print(f"   ✅ Message found in textarea: '{textarea_value}'")
                else:
                    print(f"   ❌ Textarea value: '{textarea_value}' (expected: '{test_message}')")
        except Exception as e:
            print(f"   ❌ Could not check DOM: {e}")
            
        # Try clicking send
        print("\n6. Attempting to click Send button...")
        try:
            browser.send()
            print("   ✅ send() called successfully")
        except Exception as e:
            print(f"   ❌ send() failed: {e}")
            
        print("\n7. Test complete. Browser will stay open for 5 seconds...")
        await asyncio.sleep(5)
        
    finally:
        # Cleanup
        if hasattr(browser, 'close'):
            browser.close()
            
    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)
    
    # Read the event log
    print("\n📊 Events logged:")
    log_file = Path(".runs/e2e_test.jsonl")
    if log_file.exists():
        with open(log_file) as f:
            for line in f:
                if line.strip():
                    print(f"   {line.strip()}")
    
    print("\n🔍 Common Issues:")
    print("   1. Wrong selector - textarea vs input vs div[contenteditable]")
    print("   2. Element not ready - need to wait for it")
    print("   3. Focus not set - element needs focus before typing")
    print("   4. Frame/iframe - element might be in iframe")
    print("   5. Shadow DOM - element might be in shadow root")

async def test_real_yc_page():
    """Test with the actual YC page (requires login)"""
    
    print("\n" + "="*60)
    print("TESTING WITH REAL YC PAGE")
    print("="*60)
    
    from yc_matcher.infrastructure.browser_playwright_async import BrowserAdapterPlaywrightAsync
    
    browser = BrowserAdapterPlaywrightAsync()
    
    try:
        print("1. Opening YC Cofounder Matching...")
        browser.open("https://www.startupschool.org/cofounder-matching")
        
        print("2. Waiting for page load...")
        await asyncio.sleep(3)
        
        print("3. Please manually:")
        print("   - Log in if needed")
        print("   - Navigate to a profile")
        print("   - Press Enter when ready...")
        input()
        
        print("4. Attempting to fill message...")
        test_message = "Hi! I'm interested in connecting about your startup idea."
        browser.fill_message(test_message)
        
        print("5. Check if message appeared. Press Enter to continue...")
        input()
        
        print("6. Attempting to send...")
        browser.send()
        
        print("7. Check if message was sent. Test complete.")
        
    finally:
        await asyncio.sleep(5)
        if hasattr(browser, 'close'):
            browser.close()

async def main():
    """Run tests"""
    
    print("Which test do you want to run?")
    print("1. Simple test page (no login required)")
    print("2. Real YC page (requires manual login)")
    
    choice = input("Enter 1 or 2: ").strip()
    
    if choice == "2":
        await test_real_yc_page()
    else:
        await test_message_flow()

if __name__ == "__main__":
    asyncio.run(main())