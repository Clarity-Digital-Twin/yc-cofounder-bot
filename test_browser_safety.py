#!/usr/bin/env python
"""Quick test to verify browser safety in different modes."""

import os
import sys

print("Testing browser launch safety...")

# Test 1: In test mode, should NOT launch browser
print("\n1. Test mode (should NOT launch browser):")
os.environ["PYTEST_CURRENT_TEST"] = "test_mode"

from yc_matcher.infrastructure.browser_playwright_async import PlaywrightBrowserAsync

browser = PlaywrightBrowserAsync()
print(f"   Browser runner: {browser._runner}")
assert browser._runner is None, "Runner should be None in test mode!"
print("   ✅ PASS: No browser launched in test mode")

# Clean up
del os.environ["PYTEST_CURRENT_TEST"]

# Test 2: In normal mode, should be able to launch browser
print("\n2. Normal mode (should be able to launch browser):")
from yc_matcher.infrastructure.browser_playwright_async import _shared_runner, _get_shared_runner

# Reset the global
import yc_matcher.infrastructure.browser_playwright_async as browser_module
browser_module._shared_runner = None

# Create new browser
browser2 = PlaywrightBrowserAsync()
print(f"   Browser runner: {browser2._runner}")
assert browser2._runner is not None, "Runner should exist in normal mode!"
print("   ✅ PASS: Browser can launch in normal mode")

# Clean up
if browser2._runner:
    browser2._runner.cleanup()

print("\n✅ All safety tests passed!")