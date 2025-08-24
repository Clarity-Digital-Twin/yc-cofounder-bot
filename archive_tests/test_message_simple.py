#!/usr/bin/env python3
"""
Simple synchronous test of message flow to debug the issue.
"""

import os
import sys
import time

# Setup environment
os.environ["PLAYWRIGHT_HEADLESS"] = "0"  # Show browser
os.environ["PACE_MIN_SECONDS"] = "0"  # No delays

# Add src to path
sys.path.insert(0, "src")


def test_playwright_browser():
    """Test the Playwright browser implementation"""
    print("\n" + "=" * 60)
    print("TESTING PLAYWRIGHT BROWSER")
    print("=" * 60)

    from yc_matcher.infrastructure.browser.playwright_sync import PlaywrightBrowser
    from yc_matcher.infrastructure.logging.jsonl_logger import JSONLLogger

    browser = PlaywrightBrowser()
    logger = JSONLLogger(".runs/test_simple.jsonl")
    browser.logger = logger

    try:
        # Test with a simple HTML page
        print("\n1. Creating test page with textarea...")
        test_html = """
        <html>
        <body>
            <h1>Test Message Form</h1>
            <textarea id="message" placeholder="Type your message here" style="width: 400px; height: 100px;"></textarea>
            <br><br>
            <button id="send">Send Message</button>
            <button id="invite">Invite to connect</button>
        </body>
        </html>
        """

        # Use data URL to create test page
        test_url = f"data:text/html,{test_html}"

        print("2. Opening test page...")
        success = browser.open(test_url)
        print(f"   Navigation: {'✅ SUCCESS' if success else '❌ FAILED'}")

        if not success:
            print("   Failed to open page")
            return

        # Wait for page to render
        time.sleep(2)

        # Test message filling
        test_message = "Hello! This is a test message from the debugging script."
        print(f"\n3. Attempting to fill message: '{test_message}'")

        try:
            browser.fill_message(test_message)
            print("   ✅ fill_message() called successfully")
        except Exception as e:
            print(f"   ❌ fill_message() failed: {e}")
            import traceback

            traceback.print_exc()

        # Wait to see result
        time.sleep(2)

        # Check if message appears in textarea
        print("\n4. Checking if message was filled...")
        if hasattr(browser, "page") and browser.page:
            try:
                value = browser.page.locator("#message").input_value()
                if value == test_message:
                    print(f"   ✅ Message successfully filled: '{value}'")
                else:
                    print(f"   ❌ Textarea value: '{value}' (expected: '{test_message}')")
            except Exception as e:
                print(f"   ❌ Could not check textarea: {e}")

        # Test clicking send button
        print("\n5. Attempting to click send button...")
        try:
            browser.send()
            print("   ✅ send() called successfully")
        except Exception as e:
            print(f"   ❌ send() failed: {e}")

        print("\n6. Keeping browser open for 5 seconds...")
        time.sleep(5)

    finally:
        if hasattr(browser, "close"):
            browser.close()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


def test_cua_browser():
    """Test the CUA browser implementation"""
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("CUA_MODEL"):
        print("❌ CUA not configured - skipping CUA test")
        return

    print("\n" + "=" * 60)
    print("TESTING CUA BROWSER")
    print("=" * 60)

    from yc_matcher.infrastructure.logging.jsonl_logger import JSONLLogger
    from yc_matcher.infrastructure.browser.openai_cua import OpenAICUABrowser

    browser = OpenAICUABrowser()
    logger = JSONLLogger(".runs/test_cua.jsonl")
    browser.logger = logger

    try:
        # Test with simple page
        test_html = """
        <html>
        <body>
            <h1>Test Message Form</h1>
            <textarea id="message" placeholder="Type your message here" style="width: 400px; height: 100px;"></textarea>
            <br><br>
            <button id="send">Send Message</button>
            <button id="invite">Invite to connect</button>
        </body>
        </html>
        """

        test_url = f"data:text/html,{test_html}"

        print("1. Opening test page...")
        success = browser.open(test_url)
        print(f"   Navigation: {'✅ SUCCESS' if success else '❌ FAILED'}")

        if not success:
            return

        time.sleep(2)

        # Test message filling via CUA
        test_message = "Hello from CUA! This is a test message."
        print(f"\n2. Attempting to fill message via CUA: '{test_message}'")

        try:
            browser.fill_message(test_message)
            print("   ✅ fill_message() called successfully")
        except Exception as e:
            print(f"   ❌ fill_message() failed: {e}")
            import traceback

            traceback.print_exc()

        time.sleep(3)

        # Test send
        print("\n3. Attempting to click send via CUA...")
        try:
            browser.send()
            print("   ✅ send() called successfully")
        except Exception as e:
            print(f"   ❌ send() failed: {e}")

        print("\n4. Test complete. Keeping browser open for 5 seconds...")
        time.sleep(5)

    finally:
        if hasattr(browser, "close"):
            browser.close()


def test_use_case():
    """Test the use case flow"""
    print("\n" + "=" * 60)
    print("TESTING USE CASE FLOW")
    print("=" * 60)

    from yc_matcher.application.use_cases import SendMessage
    from yc_matcher.infrastructure.browser.playwright_sync import PlaywrightBrowser
    from yc_matcher.infrastructure.logging.jsonl_logger import JSONLLogger
    from yc_matcher.infrastructure.persistence.sqlite_quota import SqliteQuotaAdapter
    from yc_matcher.infrastructure.control.stop_flag import StopFlagAdapter

    browser = PlaywrightBrowser()
    logger = JSONLLogger(".runs/test_use_case.jsonl")
    stop_flag = StopFlagAdapter()
    quota = SqliteQuotaAdapter(".runs/test_quota.sqlite")

    # Create use case
    send_message = SendMessage(browser=browser, logger=logger, stop_flag=stop_flag, quota=quota)

    # Open test page
    test_html = """
    <html>
    <body>
        <h1>Test Page</h1>
        <textarea placeholder="Message"></textarea>
        <button>Send</button>
    </body>
    </html>
    """
    browser.open(f"data:text/html,{test_html}")
    time.sleep(1)

    # Test sending message
    print("\n1. Testing send_message use case...")
    test_draft = "Test message from use case"

    try:
        result = send_message(test_draft, limit=100)
        print(f"   Result: {result}")
        if result:
            print("   ✅ Message sent successfully")
        else:
            print("   ❌ Message send failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback

        traceback.print_exc()

    time.sleep(3)
    browser.close()


def main():
    """Run tests"""
    print("Which test to run?")
    print("1. Playwright browser test")
    print("2. CUA browser test")
    print("3. Use case test")
    print("4. All tests")

    choice = input("Enter 1-4 (default 1): ").strip() or "1"

    if choice == "2":
        test_cua_browser()
    elif choice == "3":
        test_use_case()
    elif choice == "4":
        test_playwright_browser()
        test_cua_browser()
        test_use_case()
    else:
        test_playwright_browser()


if __name__ == "__main__":
    main()
