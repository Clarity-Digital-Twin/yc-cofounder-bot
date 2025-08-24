#!/usr/bin/env python3
"""
Professional debugging approach: Systematic test of message sending flow
This isolates each step to identify exactly where the failure occurs.
"""

import asyncio
import logging
import os
import sys

# Setup logging to see everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add src to path
sys.path.insert(0, 'src')

from yc_matcher.infrastructure.browser_playwright import PlaywrightBrowser
from yc_matcher.infrastructure.jsonl_logger import JSONLLogger
from yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser


class MessageFlowDebugger:
    """Systematic debugger for message sending flow"""

    def __init__(self):
        self.logger = JSONLLogger(".runs/debug_events.jsonl")
        self.results = {}

    async def test_cua_browser_flow(self):
        """Test CUA browser implementation"""
        print("\n" + "="*60)
        print("TESTING CUA BROWSER FLOW")
        print("="*60)

        if not os.getenv("OPENAI_API_KEY") or not os.getenv("CUA_MODEL"):
            print("❌ CUA not configured - skipping")
            self.results["cua_browser"] = "SKIPPED - No API key/model"
            return

        try:
            browser = OpenAICUABrowser()
            browser.logger = self.logger

            # Step 1: Navigation
            print("\n1. Testing navigation...")
            url = "https://www.startupschool.org/cofounder-matching"
            success = browser.open(url)
            print(f"   Navigation: {'✅ SUCCESS' if success else '❌ FAILED'}")
            self.results["cua_navigate"] = success

            if not success:
                return

            # Step 2: Fill message using CUA
            print("\n2. Testing message fill via CUA...")
            test_message = "Hi! I'm interested in connecting about your startup."

            # Try the fill_message method
            try:
                browser.fill_message(test_message)
                print("   fill_message() called: ✅")
                self.results["cua_fill_message"] = "CALLED"
            except Exception as e:
                print(f"   fill_message() failed: ❌ {e}")
                self.results["cua_fill_message"] = f"ERROR: {e}"

            # Also try direct CUA action
            print("\n3. Testing direct CUA action for message...")
            try:
                result = await browser._cua_action(
                    f"Type this message in the message box: {test_message}"
                )
                print(f"   CUA action result: {result}")
                self.results["cua_direct_action"] = result
            except Exception as e:
                print(f"   CUA action failed: ❌ {e}")
                self.results["cua_direct_action"] = f"ERROR: {e}"

        except Exception as e:
            print(f"❌ CUA Browser Error: {e}")
            self.results["cua_browser"] = f"ERROR: {e}"

    async def test_playwright_flow(self):
        """Test Playwright-only browser implementation"""
        print("\n" + "="*60)
        print("TESTING PLAYWRIGHT FLOW")
        print("="*60)

        try:
            browser = PlaywrightBrowser()
            browser.logger = self.logger

            # Step 1: Navigation
            print("\n1. Testing navigation...")
            url = "https://www.startupschool.org/cofounder-matching"
            success = browser.open(url)
            print(f"   Navigation: {'✅ SUCCESS' if success else '❌ FAILED'}")
            self.results["playwright_navigate"] = success

            if not success:
                return

            # Step 2: Fill message
            print("\n2. Testing message fill...")
            test_message = "Hi! I'm interested in connecting about your startup."

            try:
                browser.fill_message(test_message)
                print("   fill_message() called: ✅")
                self.results["playwright_fill_message"] = "SUCCESS"
            except Exception as e:
                print(f"   fill_message() failed: ❌ {e}")
                self.results["playwright_fill_message"] = f"ERROR: {e}"

            # Step 3: Check DOM for message
            print("\n3. Checking if message is in DOM...")
            try:
                # Get page content
                if hasattr(browser, 'page') and browser.page:
                    content = browser.page.content()
                    if test_message in content:
                        print("   Message found in DOM: ✅")
                        self.results["playwright_dom_check"] = "FOUND"
                    else:
                        print("   Message NOT in DOM: ❌")
                        self.results["playwright_dom_check"] = "NOT_FOUND"
            except Exception as e:
                print(f"   DOM check failed: {e}")
                self.results["playwright_dom_check"] = f"ERROR: {e}"

        except Exception as e:
            print(f"❌ Playwright Browser Error: {e}")
            self.results["playwright_browser"] = f"ERROR: {e}"

    async def test_use_case_flow(self):
        """Test the use case orchestration"""
        print("\n" + "="*60)
        print("TESTING USE CASE FLOW")
        print("="*60)

        from yc_matcher.application.use_cases import ProcessCandidateUseCase
        from yc_matcher.infrastructure.sqlite_quota import SqliteQuotaAdapter
        from yc_matcher.infrastructure.sqlite_repo import SqliteRepoAdapter
        from yc_matcher.infrastructure.stop_flag import StopFlagAdapter

        try:
            # Setup dependencies
            browser = PlaywrightBrowser()
            logger = self.logger
            stop_flag = StopFlagAdapter()
            seen_repo = SqliteRepoAdapter(".runs/test_seen.sqlite")
            quota = SqliteQuotaAdapter(".runs/test_quota.sqlite")

            use_case = ProcessCandidateUseCase(
                browser=browser,
                logger=logger,
                stop_flag=stop_flag,
                seen_repo=seen_repo,
                quota=quota
            )

            # Test the send_message method
            print("\n1. Testing send_message method...")
            test_draft = "Test message from use case"
            test_profile_id = "test_profile_123"

            try:
                # Mock navigation first
                browser.open("https://www.startupschool.org/cofounder-matching")

                # Call send_message
                result = use_case.send_message(test_draft, test_profile_id)
                print(f"   send_message result: {result}")
                self.results["use_case_send"] = result
            except Exception as e:
                print(f"   send_message failed: ❌ {e}")
                self.results["use_case_send"] = f"ERROR: {e}"

        except Exception as e:
            print(f"❌ Use Case Error: {e}")
            self.results["use_case"] = f"ERROR: {e}"

    def print_summary(self):
        """Print systematic analysis summary"""
        print("\n" + "="*60)
        print("SYSTEMATIC ANALYSIS SUMMARY")
        print("="*60)

        print("\n📊 Test Results:")
        for key, value in self.results.items():
            status = "✅" if value or value == "SUCCESS" else "❌"
            print(f"   {status} {key}: {value}")

        print("\n🔍 Root Cause Analysis:")

        # Analyze patterns
        if "cua_fill_message" in self.results and "ERROR" in str(self.results.get("cua_fill_message", "")):
            print("   ⚠️  CUA fill_message implementation has issues")
            print("      → Check _fill_message_async() in openai_cua_browser.py")

        if "playwright_fill_message" in self.results and "ERROR" in str(self.results.get("playwright_fill_message", "")):
            print("   ⚠️  Playwright fill_message implementation has issues")
            print("      → Check selector logic in browser_playwright.py")

        if self.results.get("playwright_dom_check") == "NOT_FOUND":
            print("   ⚠️  Message not appearing in DOM after fill")
            print("      → Selector may be wrong or page structure changed")

        print("\n📝 Next Steps:")
        print("   1. Check browser DevTools for actual textarea/input selectors")
        print("   2. Add explicit waits for elements before filling")
        print("   3. Log actual CUA actions being executed")
        print("   4. Compare with working version git history")

async def main():
    """Run systematic debugging"""
    debugger = MessageFlowDebugger()

    # Run tests based on environment
    if os.getenv("ENABLE_CUA") == "1":
        await debugger.test_cua_browser_flow()
    else:
        print("ℹ️  CUA disabled, testing Playwright only")

    await debugger.test_playwright_flow()
    await debugger.test_use_case_flow()

    debugger.print_summary()

    # Write detailed logs
    print("\n📄 Detailed logs written to: .runs/debug_events.jsonl")

if __name__ == "__main__":
    asyncio.run(main())
