#!/usr/bin/env python3
"""
Professional send pipeline test with full observability.
This implements the exact trace pattern to diagnose send failures.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, "src")

# Configure environment
os.environ["PACE_MIN_SECONDS"] = "0"
os.environ["SHADOW_MODE"] = "0"  # Ensure we actually try to send


def test_pure_playwright_send():
    """Test ONLY the send pipeline with forced YES decision - no NLP."""
    print("\n" + "=" * 60)
    print("PURE PLAYWRIGHT SEND TEST (No NLP)")
    print("=" * 60)

    import os

    # Set browser path
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = ".ms-playwright"

    from yc_matcher.infrastructure.browser_observable import ObservableBrowser
    from yc_matcher.infrastructure.browser_playwright_async import PlaywrightBrowserAsync
    from yc_matcher.infrastructure.jsonl_logger import JSONLLogger
    from yc_matcher.infrastructure.send_pipeline_observer import SendPipelineObserver

    # Setup
    logger = JSONLLogger(".runs/pipeline_test.jsonl")
    observer = SendPipelineObserver(logger)
    base_browser = PlaywrightBrowserAsync()
    browser = ObservableBrowser(base_browser, observer)

    print(f"\nRun ID: {observer.run_id}")
    print("Events will be logged to: .runs/pipeline_test.jsonl")

    # 1. Navigate
    print("\n1. Opening YC page...")
    success = browser.open("https://www.startupschool.org/cofounder-matching")
    print(f"   Navigation: {'✅' if success else '❌'}")

    if not success:
        print("   Failed to navigate. Check browser installation.")
        return

    print("\n2. MANUAL STEP REQUIRED:")
    print("   - Log in if needed")
    print("   - Navigate to a specific profile")
    print("   - Ensure you see the message box")
    print("\n   Press Enter when ready...")
    input()

    # Start new profile
    profile_num = observer.new_profile()
    print(f"\n3. Testing profile #{profile_num}")

    # Simulate profile extraction
    observer.profile_extracted("Fake profile text for testing")

    # FORCE a YES decision with auto_send
    print("\n4. Forcing YES decision with auto_send=true")
    observer.decision_request("test-stub", "stub input")
    time.sleep(0.1)  # Simulate latency
    observer.decision_response(
        decision="YES",
        auto_send=True,
        output_types=["message"],
        latency_ms=100,
        decision_json_ok=True,
    )

    # Check gates
    print("\n5. Checking send gates...")
    from yc_matcher.infrastructure.sqlite_quota import SqliteQuotaAdapter
    from yc_matcher.infrastructure.sqlite_repo import SqliteRepoAdapter
    from yc_matcher.infrastructure.stop_flag import StopFlagAdapter

    stop_flag = StopFlagAdapter()
    quota = SqliteQuotaAdapter(".runs/test_quota.sqlite")
    seen_repo = SqliteRepoAdapter(".runs/test_seen.sqlite")

    stop_is_set = stop_flag.is_stopped()
    quota_ok = quota.check_and_increment(1)
    seen_ok = not seen_repo.has_seen("test_profile_hash")

    observer.send_gate(
        stop=stop_is_set,
        quota_ok=quota_ok,
        seen_ok=seen_ok,
        mode="test",
        auto_send=True,
        remaining_quota=quota.remaining() if hasattr(quota, "remaining") else 99,
    )

    print(f"   Stop flag: {'❌ SET' if stop_is_set else '✅ clear'}")
    print(f"   Quota: {'✅ OK' if quota_ok else '❌ BLOCKED'}")
    print(f"   Seen: {'✅ OK' if seen_ok else '❌ DUPLICATE'}")

    if stop_is_set or not quota_ok or not seen_ok:
        print("\n⚠️  Gates are blocking! Check stop flag, quota, or dedup.")
        return

    # Now test the actual send pipeline
    test_message = f"TEST MESSAGE {datetime.now().strftime('%H:%M:%S')}"
    print(f"\n6. Testing send pipeline with: '{test_message}'")

    # Focus
    print("   a. Focusing message box...")
    browser.focus_message_box()
    time.sleep(0.5)

    # Fill
    print("   b. Filling message...")
    browser.fill_message(test_message)
    time.sleep(0.5)

    # Send
    print("   c. Clicking send...")
    browser.send()
    time.sleep(1)

    # Verify
    print("   d. Verifying sent...")
    sent_ok = browser.verify_sent()

    if sent_ok:
        observer.sent()
        print("   ✅ MESSAGE SENT SUCCESSFULLY!")
    else:
        print("   ❌ Verification failed")

    # Analyze the pipeline
    print("\n7. Pipeline Analysis:")
    analyze_pipeline_log()

    print("\n8. Press Enter to close browser...")
    input()
    browser.close()


def test_with_real_decision():
    """Test with actual AI decision."""
    print("\n" + "=" * 60)
    print("FULL PIPELINE TEST (With AI Decision)")
    print("=" * 60)

    from yc_matcher.domain.entities import Criteria, Profile
    from yc_matcher.infrastructure.browser_observable import ObservableBrowser
    from yc_matcher.infrastructure.jsonl_logger import JSONLLogger
    from yc_matcher.infrastructure.openai_decision import OpenAIDecisionAdapter
    from yc_matcher.infrastructure.send_pipeline_observer import SendPipelineObserver

    # Check if OpenAI is configured
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set")
        return

    # Setup
    logger = JSONLLogger(".runs/pipeline_full.jsonl")
    observer = SendPipelineObserver(logger)

    # Choose browser
    if os.getenv("ENABLE_CUA") == "1":
        from yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser

        base_browser = OpenAICUABrowser()
        print("Using CUA Browser")
    else:
        from yc_matcher.infrastructure.browser_playwright_async import PlaywrightBrowserAsync

        base_browser = PlaywrightBrowserAsync()
        print("Using Playwright Browser")

    browser = ObservableBrowser(base_browser, observer)

    print(f"\nRun ID: {observer.run_id}")

    # Navigate and get profile
    print("\n1. Opening YC page...")
    browser.open("https://www.startupschool.org/cofounder-matching")

    print("\n2. Navigate to a profile manually.")
    print("   Press Enter when ready...")
    input()

    # Read profile
    profile_num = observer.new_profile()
    print(f"\n3. Reading profile #{profile_num}...")

    profile_text = browser.read_profile_text()
    if not profile_text:
        print("   ❌ Could not read profile")
        return

    print(f"   Profile extracted: {len(profile_text)} chars")

    # Get decision
    print("\n4. Getting AI decision...")

    from openai import OpenAI

    client = OpenAI()
    decision_adapter = OpenAIDecisionAdapter(client, logger=logger)

    profile = Profile(raw_text=profile_text)
    criteria = Criteria(
        text="""
    Looking for technical co-founders with:
    - Strong engineering background
    - Startup experience
    - Located in SF Bay Area

    Message Template:
    Hi! I noticed your profile and your experience with [specific thing from profile].
    I'm working on [my startup] and looking for a technical co-founder.
    Would love to connect and discuss potential collaboration!
    """
    )

    observer.decision_request(
        model=os.getenv("OPENAI_DECISION_MODEL", "gpt-4"), input_text=profile_text + criteria.text
    )

    start_time = time.time()
    evaluation = decision_adapter.evaluate(profile, criteria)
    latency_ms = int((time.time() - start_time) * 1000)

    # Log decision response
    output_types = ["message"]  # Default for GPT-4
    if "gpt-5" in str(os.getenv("OPENAI_DECISION_MODEL", "")):
        output_types = evaluation.get("_output_types", ["reasoning", "message"])

    observer.decision_response(
        decision=evaluation.get("decision", "ERROR"),
        auto_send=evaluation.get("auto_send", False),
        output_types=output_types,
        latency_ms=latency_ms,
        decision_json_ok=evaluation.get("decision") in ["YES", "NO"],
    )

    print(f"   Decision: {evaluation.get('decision')}")
    print(f"   Auto-send: {evaluation.get('auto_send')}")

    # Check if should send
    if evaluation.get("decision") != "YES":
        print("\n   Decision was NO - not sending")
        return

    if not evaluation.get("auto_send"):
        print("\n   ⚠️  auto_send is False! Check AI prompt/schema.")
        return

    # Continue with send pipeline...
    draft = evaluation.get("draft", "")
    if not draft:
        print("\n   ❌ No draft message generated")
        return

    print(f"\n5. Sending message ({len(draft)} chars)...")

    # Check gates and send (same as before)
    # ... (rest of send logic)

    browser.close()


def analyze_pipeline_log():
    """Analyze the pipeline log to find issues."""
    log_file = Path(".runs/pipeline_test.jsonl")
    if not log_file.exists():
        print("   No log file found")
        return

    events = []
    with open(log_file) as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except Exception:
                    pass

    # Find the latest run
    if not events:
        print("   No events logged")
        return

    latest_run = events[-1].get("run_id")
    run_events = [e for e in events if e.get("run_id") == latest_run]

    # Check pipeline order
    expected_order = [
        "profile_extracted",
        "decision_request",
        "decision_response",
        "send_gate",
        "focus_message_box_result",
        "fill_message_result",
        "click_send_result",
        "verify_sent_attempt",
        "verify_sent_result",
    ]

    actual_order = [e["event"] for e in run_events if e["event"] in expected_order]

    print(f"\n   Expected: {' → '.join(expected_order)}")
    print(f"   Actual:   {' → '.join(actual_order)}")

    # Find where it stopped
    for i, expected in enumerate(expected_order):
        if i >= len(actual_order):
            print(f"\n   ⚠️  Pipeline stopped at: {expected_order[i - 1] if i > 0 else 'START'}")
            print(f"   Missing: {expected}")
            break
        elif actual_order[i] != expected:
            print(f"\n   ⚠️  Unexpected event: got {actual_order[i]}, expected {expected}")
            break

    # Check for failures
    for event in run_events:
        if not event.get("ok"):
            print(f"\n   ❌ Failed: {event['event']}")
            if event.get("error"):
                print(f"      Error: {event['error']}")
            if event.get("selector_used"):
                print(f"      Selector: {event['selector_used']}")


def main():
    print("Professional Send Pipeline Test")
    print("================================")
    print("\nOptions:")
    print("1. Pure Playwright test (no AI, forced YES)")
    print("2. Full test with real AI decision")
    print("3. Analyze existing logs")

    choice = input("\nEnter 1-3: ").strip()

    if choice == "2":
        test_with_real_decision()
    elif choice == "3":
        analyze_pipeline_log()
    else:
        test_pure_playwright_send()


if __name__ == "__main__":
    main()
