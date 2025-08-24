#!/usr/bin/env python3
"""
Test the actual message flow to see where it's failing.
This mimics what the real app does.
"""

import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, "src")

# Setup environment
os.environ["PACE_MIN_SECONDS"] = "0"
os.environ["ENABLE_CUA"] = "1"  # or "0" to test Playwright


def test_send_message_flow():
    """Test the SendMessage use case directly"""
    print("\n" + "=" * 60)
    print("TESTING SEND MESSAGE FLOW")
    print("=" * 60)

    from yc_matcher.application.use_cases import SendMessage
    from yc_matcher.infrastructure.jsonl_logger import JSONLLogger
    from yc_matcher.infrastructure.sqlite_quota import SqliteQuotaAdapter
    from yc_matcher.infrastructure.stop_flag import StopFlagAdapter

    # Choose browser based on ENABLE_CUA
    if os.getenv("ENABLE_CUA") == "1":
        print("Using CUA Browser...")
        from yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser

        browser = OpenAICUABrowser()
    else:
        print("Using Playwright Browser...")
        from yc_matcher.infrastructure.browser_playwright_async import PlaywrightBrowserAsync

        browser = PlaywrightBrowserAsync()

    # Setup components
    logger = JSONLLogger(".runs/test_flow_events.jsonl")
    stop_flag = StopFlagAdapter()
    quota = SqliteQuotaAdapter(".runs/test_quota.sqlite")

    # Log setup
    logger.emit({"event": "test_start", "browser": browser.__class__.__name__})

    # Create SendMessage use case
    send_message = SendMessage(browser=browser, logger=logger, stop_flag=stop_flag, quota=quota)

    print("\n1. Opening YC Cofounder page...")
    try:
        success = browser.open("https://www.startupschool.org/cofounder-matching")
        print(f"   Navigation: {'✅ SUCCESS' if success else '❌ FAILED'}")
        logger.emit({"event": "navigation", "success": success})
    except Exception as e:
        print(f"   ❌ Navigation error: {e}")
        logger.emit({"event": "navigation_error", "error": str(e)})
        return

    print("\n2. Manual Step Required:")
    print("   Please manually:")
    print("   - Log in to YC if needed")
    print("   - Navigate to a specific profile")
    print("   - Make sure you see the message box")
    print("\n   Press Enter when ready...")
    input()

    # Test message
    test_message = """Hi! I noticed your profile and I'm really interested in your startup idea.
I have experience in similar technologies and would love to connect to discuss potential collaboration.
Looking forward to hearing from you!"""

    print("\n3. Attempting to send message...")
    print(f"   Message: {test_message[:50]}...")

    try:
        # This calls the actual flow: focus -> fill -> send -> verify
        result = send_message(test_message, limit=100)

        print(f"\n   Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
        logger.emit({"event": "send_result", "success": result})

    except Exception as e:
        print(f"   ❌ Error during send: {e}")
        logger.emit({"event": "send_error", "error": str(e)})
        import traceback

        traceback.print_exc()

    print("\n4. Analyzing logs...")
    print_event_log()

    print("\n5. Press Enter to close browser...")
    input()

    if hasattr(browser, "close"):
        browser.close()


def print_event_log():
    """Print the event log for analysis"""
    log_file = Path(".runs/test_flow_events.jsonl")
    if not log_file.exists():
        print("   No events logged")
        return

    print("\n📊 Event Log:")
    with open(log_file) as f:
        for line in f:
            if line.strip():
                try:
                    event = json.loads(line)
                    event_type = event.get("event", "unknown")

                    # Highlight important events
                    if event_type in ["send_result", "send_error", "stopped"]:
                        print(f"   ⚠️  {event_type}: {event}")
                    elif event_type in ["focus_message_box", "fill_message", "send", "verify_sent"]:
                        print(f"   ➡️  {event_type}: {event}")
                    else:
                        print(f"      {event_type}: {event}")
                except Exception:
                    print(f"      {line.strip()}")


def test_browser_methods_directly():
    """Test browser methods one by one"""
    print("\n" + "=" * 60)
    print("TESTING BROWSER METHODS DIRECTLY")
    print("=" * 60)

    if os.getenv("ENABLE_CUA") == "1":
        from yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser

        browser = OpenAICUABrowser()
        print("Using CUA Browser")
    else:
        from yc_matcher.infrastructure.browser_playwright_async import PlaywrightBrowserAsync

        browser = PlaywrightBrowserAsync()
        print("Using Playwright Browser")

    print("\n1. Opening page...")
    browser.open("https://www.startupschool.org/cofounder-matching")

    print("\n2. Please navigate to a profile manually.")
    print("   Press Enter when ready...")
    input()

    test_message = "Test message for debugging"

    print("\n3. Testing focus_message_box()...")
    try:
        browser.focus_message_box()
        print("   ✅ Focus succeeded")
    except Exception as e:
        print(f"   ❌ Focus failed: {e}")

    print("\n4. Testing fill_message()...")
    try:
        browser.fill_message(test_message)
        print("   ✅ Fill succeeded")
        print("   Check if message appears in the box!")
    except Exception as e:
        print(f"   ❌ Fill failed: {e}")

    print("\n5. Press Enter to test send()...")
    input()

    try:
        browser.send()
        print("   ✅ Send succeeded")
    except Exception as e:
        print(f"   ❌ Send failed: {e}")

    print("\n6. Testing verify_sent()...")
    try:
        result = browser.verify_sent()
        print(f"   Verify result: {result}")
    except Exception as e:
        print(f"   ❌ Verify failed: {e}")

    print("\n7. Press Enter to close...")
    input()
    browser.close()


def main():
    print("Which test to run?")
    print("1. Test full SendMessage flow")
    print("2. Test browser methods directly")

    choice = input("Enter 1 or 2: ").strip()

    if choice == "2":
        test_browser_methods_directly()
    else:
        test_send_message_flow()


if __name__ == "__main__":
    main()
