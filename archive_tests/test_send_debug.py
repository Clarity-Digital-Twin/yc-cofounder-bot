#!/usr/bin/env python3
"""
TEMPORARY DEBUG SCRIPT - DELETE AFTER FIXING
Direct test of the send pipeline to diagnose why messages aren't being sent.
Uses the 10-event observability pattern to pinpoint exact failure.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Load .env file properly (handles special characters like $ in password)
env_file = Path(".env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                # Don't override if already set (e.g., from command line)
                if key not in os.environ:
                    os.environ[key] = value
                    if key == "YC_PASSWORD":
                        print(f"DEBUG: Loaded password with {len(value)} chars")

# Setup environment
os.environ["PACE_MIN_SECONDS"] = "0"
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = ".ms-playwright"
os.environ["PLAYWRIGHT_HEADLESS"] = "0"  # Show browser for debugging
os.environ["SHADOW_MODE"] = "0"  # Actually try to send!
os.environ["ENABLE_CUA"] = "0"  # Use Playwright

# Add src to path
sys.path.insert(0, "src")


def main():
    """Run the full send pipeline with observability."""
    print("\n" + "=" * 60)
    print("SEND PIPELINE DEBUG TEST")
    print("=" * 60)

    # Setup observability
    from pathlib import Path

    from yc_matcher.application.use_cases import SendMessage
    from yc_matcher.infrastructure.browser.observable import ObservableBrowser
    from yc_matcher.infrastructure.browser.playwright_async import PlaywrightBrowserAsync
    from yc_matcher.infrastructure.logging.jsonl_logger import JSONLLogger
    from yc_matcher.infrastructure.logging.pipeline_observer import SendPipelineObserver
    from yc_matcher.infrastructure.persistence.sqlite_quota import SQLiteDailyWeeklyQuota
    from yc_matcher.infrastructure.control.stop_flag import FileStopFlag

    log_path = Path(".runs/debug_pipeline.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = JSONLLogger(log_path)
    observer = SendPipelineObserver(logger)
    base_browser = PlaywrightBrowserAsync()
    browser = ObservableBrowser(base_browser, observer)

    print(f"Run ID: {observer.run_id}")
    print("Events logged to: .runs/debug_pipeline.jsonl")

    # 1. Navigate to YC
    print("\n1. Opening YC Cofounder Matching...")
    success = browser.open("https://www.startupschool.org/cofounder-matching")

    if not success:
        print("❌ Failed to navigate")
        return

    print("✅ Navigation successful")
    time.sleep(3)

    # 2. Check login
    print("\n2. Checking login status...")
    is_logged_in = base_browser.is_logged_in()

    if not is_logged_in:
        print("⚠️  Not logged in. Waiting 30 seconds for manual login...")
        print("   Please log in manually in the browser window")
        time.sleep(30)

        is_logged_in = base_browser.is_logged_in()
        if not is_logged_in:
            print("❌ Still not logged in. Exiting.")
            return

    print("✅ Logged in")

    # 3. Navigate to cofounder matching (mimicking actual flow)
    print("\n3. Navigating to cofounder matching...")
    yc_url = "https://www.startupschool.org/cofounder-matching"
    print(f"   Opening: {yc_url}")
    browser.open(yc_url)
    time.sleep(3)

    # Check if we're logged in after navigation
    is_logged_in = base_browser.is_logged_in()
    if not is_logged_in:
        print("❌ Lost login after navigation")
        return
    print("✅ Still logged in after navigation")

    # 4. Click View Profile (using the exact same logic as the codebase)
    print("\n4. Attempting to view a profile...")
    profile_num = observer.new_profile()

    # The code calls click_view_profile which handles all the logic
    clicked = browser.click_view_profile()
    if not clicked:
        print("❌ Could not click View Profile")

        # Get current URL for debugging
        if hasattr(base_browser, "_runner") and base_browser._runner:
            try:
                page = base_browser._ensure_page()
                if page:
                    print(f"   Current URL: {page.url}")
            except Exception:
                pass

        print("   Please manually:")
        print("   1. If you see 'View Profiles' button, click it")
        print("   2. Then click on a specific profile")
        print("   3. Press Enter when you see a profile with a message box...")
        input()
    else:
        print(f"✅ Viewing profile #{profile_num}")
        time.sleep(2)

    # 5. Extract profile
    print("\n5. Extracting profile text...")
    profile_text = browser.read_profile_text()

    if profile_text:
        print(f"✅ Extracted {len(profile_text)} chars")
        observer.profile_extracted(profile_text)
    else:
        print("⚠️  No profile text extracted")

    # 6. Simulate decision (force YES)
    print("\n6. Simulating AI decision...")
    observer.decision_request("gpt-4", "test-input")
    time.sleep(0.1)

    observer.decision_response(
        decision="YES",
        auto_send=True,
        output_types=["message"],
        latency_ms=100,
        decision_json_ok=True,
    )
    print("✅ Decision: YES (forced)")
    print("✅ Auto-send: True")

    # 7. Check gates
    print("\n7. Checking send gates...")
    stop_flag = FileStopFlag()
    quota = SQLiteDailyWeeklyQuota(".runs/debug_quota.sqlite")

    stop_is_set = stop_flag.is_stopped()
    quota_ok = quota.check_and_increment(1)

    observer.send_gate(
        stop=stop_is_set,
        quota_ok=quota_ok,
        seen_ok=True,
        mode="debug",
        auto_send=True,
        remaining_quota=99,
    )

    print(f"   Stop flag: {'SET ❌' if stop_is_set else 'clear ✅'}")
    print(f"   Quota: {'OK ✅' if quota_ok else 'BLOCKED ❌'}")

    if stop_is_set or not quota_ok:
        print("\n❌ Gates blocking send")
        return

    # 8. THE ACTUAL SEND PIPELINE
    test_message = f"""Hi! I noticed your technical background and startup experience.
I'm building an AI platform and looking for a technical co-founder.
Would love to connect and discuss potential collaboration!
[DEBUG TEST {datetime.now().strftime("%H:%M:%S")}]"""

    print("\n8. Testing send pipeline...")
    print(f"   Message: {test_message[:50]}...")

    # Using SendMessage use case (the real flow)
    SendMessage(browser=base_browser, logger=logger, stop=stop_flag, quota=quota)

    print("\n   === SEND PIPELINE STEPS ===")

    # A. Focus message box
    print("   A. Focusing message box...")
    try:
        browser.focus_message_box()
        print("      ✅ Focus succeeded")
        time.sleep(0.5)
    except Exception as e:
        print(f"      ❌ Focus failed: {e}")

    # B. Fill message
    print("   B. Filling message...")
    try:
        browser.fill_message(test_message)
        print("      ✅ Fill succeeded")
        print("      CHECK: Is the message visible in the text box?")
        time.sleep(1)
    except Exception as e:
        print(f"      ❌ Fill failed: {e}")

    # C. Click send button
    print("   C. Clicking send button...")
    print("      Looking for: 'Invite to connect' or 'Send' button")
    try:
        browser.send()
        print("      ✅ Send clicked")
        time.sleep(2)
    except Exception as e:
        print(f"      ❌ Send failed: {e}")

    # D. Verify sent
    print("   D. Verifying message was sent...")
    try:
        sent_ok = browser.verify_sent()
        if sent_ok:
            observer.sent()
            print("      ✅ MESSAGE SENT SUCCESSFULLY!")
        else:
            print("      ❌ Verification failed")
            print("      Message may not have been sent")
    except Exception as e:
        print(f"      ❌ Verify failed: {e}")

    # 9. Analyze the pipeline
    print("\n9. PIPELINE ANALYSIS:")
    print("-" * 50)
    analyze_events(".runs/debug_pipeline.jsonl", observer.run_id)

    print("\n10. Browser will stay open for inspection...")
    print("   Press Enter to close and exit...")
    input()

    # Cleanup
    if hasattr(base_browser, "cleanup"):
        base_browser.cleanup()


def analyze_events(log_path, run_id):
    """Analyze the 10-event pipeline."""
    log_file = Path(log_path)
    if not log_file.exists():
        print("No log file found")
        return

    events = []
    with open(log_file) as f:
        for line in f:
            if line.strip():
                try:
                    event = json.loads(line)
                    if event.get("run_id") == run_id:
                        events.append(event)
                except Exception:
                    pass

    # Expected pipeline events
    pipeline = [
        "profile_extracted",
        "decision_request",
        "decision_response",
        "send_gate",
        "focus_message_box_result",
        "fill_message_result",
        "click_send_result",
        "verify_sent_attempt",
        "verify_sent_result",
        "sent",
    ]

    print("\n10-EVENT PIPELINE STATUS:")
    for expected in pipeline:
        matching = [e for e in events if e.get("event") == expected]
        if matching:
            event = matching[0]
            if event.get("ok") is False:
                print(f"  {expected:30} ❌ FAILED")
                if event.get("error"):
                    print(f"    Error: {event['error']}")
                if event.get("selector_used"):
                    print(f"    Selector tried: {event['selector_used']}")
            else:
                print(f"  {expected:30} ✅")
                if event.get("selector_used"):
                    print(f"    Used: {event['selector_used']}")
                if event.get("button_variant"):
                    print(f"    Button: {event['button_variant']}")
        else:
            print(f"  {expected:30} ⚠️  MISSING")

    # Find the failure point
    print("\nFAILURE POINT:")
    for i, expected in enumerate(pipeline):
        matching = [e for e in events if e.get("event") == expected]
        if not matching or (matching and matching[0].get("ok") is False):
            print(f"  Pipeline failed at step {i + 1}: {expected}")
            if i > 0:
                print(f"  Last successful step: {pipeline[i - 1]}")
            break
    else:
        print("  All steps completed successfully!")


if __name__ == "__main__":
    main()
