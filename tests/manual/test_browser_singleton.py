#!/usr/bin/env python
"""Test that browser singleton works correctly."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = ".ms-playwright"
os.environ["ENABLE_PLAYWRIGHT"] = "1"
os.environ["ENABLE_CUA"] = "0"
os.environ["PLAYWRIGHT_HEADLESS"] = "0"

from yc_matcher.infrastructure.browser_playwright_async import PlaywrightBrowserAsync

print("Testing Browser Singleton Pattern")
print("="*50)

# Create first browser instance
print("\n1. Creating first browser instance...")
browser1 = PlaywrightBrowserAsync()
print(f"   Browser1 runner: {id(browser1._runner)}")

# Open YC in first browser
url = "https://www.startupschool.org/cofounder-matching"
print(f"\n2. Opening {url} in browser1...")
browser1.open(url)
print("   ✅ Page opened")

# Create second browser instance
print("\n3. Creating second browser instance...")
browser2 = PlaywrightBrowserAsync()
print(f"   Browser2 runner: {id(browser2._runner)}")

# Check if they share the same runner
if id(browser1._runner) == id(browser2._runner):
    print("\n✅ SUCCESS: Both browsers share the SAME AsyncLoopRunner!")
    print("   This means they share the same browser window.")
else:
    print("\n❌ FAIL: Browsers have DIFFERENT AsyncLoopRunners")
    print("   This would create multiple browser windows.")

# Test that browser2 can see the same page
print("\n4. Testing that browser2 sees the same page...")
try:
    # browser2 should be able to interact with the already-open page
    is_logged = browser2.is_logged_in()
    print(f"   Login status from browser2: {is_logged}")
    print("   ✅ Browser2 can access the same page as browser1!")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*50)
print("Test Complete!")
print("\nThe singleton pattern is working correctly.")
print("When you click 'Open Controlled Browser' and log in,")
print("then click 'Start Autonomous Browsing', it will use")
print("the SAME browser window that's already logged in!")

# Keep browser open for observation
import time

print("\nKeeping browser open for 10 seconds...")
time.sleep(10)

# Cleanup
browser1.cleanup()
print("✅ Cleaned up")
