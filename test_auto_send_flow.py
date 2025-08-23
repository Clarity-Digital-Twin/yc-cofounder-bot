#!/usr/bin/env python3
"""
Automated send flow test with full pipeline observability.
This test automatically navigates, evaluates, and attempts to send.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

# Configure environment
os.environ["PACE_MIN_SECONDS"] = "0"
os.environ["SHADOW_MODE"] = "0"  
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = ".ms-playwright"
os.environ["PLAYWRIGHT_HEADLESS"] = "0"  # Show browser for debugging

def test_full_auto_flow():
    """Test the complete flow automatically."""
    print("\n" + "="*60)
    print("AUTOMATED SEND FLOW TEST")
    print("="*60)
    
    from yc_matcher.infrastructure.browser_playwright_async import PlaywrightBrowserAsync
    from yc_matcher.infrastructure.jsonl_logger import JSONLLogger
    from yc_matcher.infrastructure.send_pipeline_observer import SendPipelineObserver
    from yc_matcher.infrastructure.browser_observable import ObservableBrowser
    from yc_matcher.application.use_cases import SendMessage
    from yc_matcher.infrastructure.stop_flag import FileStopFlag
    from yc_matcher.infrastructure.sqlite_quota import SQLiteDailyWeeklyQuota
    
    # Setup
    logger = JSONLLogger(".runs/auto_flow_test.jsonl")
    observer = SendPipelineObserver(logger)
    base_browser = PlaywrightBrowserAsync()
    browser = ObservableBrowser(base_browser, observer)
    
    print(f"\nRun ID: {observer.run_id}")
    print("Events will be logged to: .runs/auto_flow_test.jsonl")
    
    # 1. Navigate
    print("\n1. Opening YC page...")
    success = browser.open("https://www.startupschool.org/cofounder-matching")
    print(f"   Navigation: {'✅' if success else '❌'}")
    
    if not success:
        print("   Failed to navigate. Check browser installation.")
        return
    
    # Wait for page to load
    time.sleep(3)
    
    # 2. Check if logged in
    print("\n2. Checking login status...")
    is_logged_in = base_browser.is_logged_in()
    print(f"   Logged in: {'✅' if is_logged_in else '❌'}")
    
    if not is_logged_in:
        print("\n   ⚠️  Not logged in. Please log in manually.")
        print("   Waiting 20 seconds for manual login...")
        time.sleep(20)
        
        # Check again
        is_logged_in = base_browser.is_logged_in()
        if not is_logged_in:
            print("   Still not logged in. Exiting.")
            return
    
    # 3. Try to navigate to a profile
    print("\n3. Attempting to view a profile...")
    profile_num = observer.new_profile()
    
    profile_clicked = browser.click_view_profile()
    if profile_clicked:
        print(f"   ✅ Viewing profile #{profile_num}")
        
        # Extract profile text
        time.sleep(2)  # Let profile load
        profile_text = browser.read_profile_text()
        
        if profile_text:
            print(f"   ✅ Profile extracted: {len(profile_text)} chars")
            observer.profile_extracted(profile_text)
        else:
            print("   ❌ Could not extract profile text")
    else:
        print("   ❌ Could not click View Profile button")
        print("   Current page may not have profiles available")
    
    # 4. Simulate decision (force YES for testing)
    print("\n4. Simulating AI decision...")
    observer.decision_request("test-model", "test-input")
    time.sleep(0.1)
    
    # Force YES with auto_send
    observer.decision_response(
        decision="YES",
        auto_send=True,
        output_types=["message"],
        latency_ms=100,
        decision_json_ok=True
    )
    print("   ✅ Decision: YES (forced for testing)")
    print("   ✅ Auto-send: True")
    
    # 5. Check send gates
    print("\n5. Checking send gates...")
    stop_flag = FileStopFlag()
    quota = SQLiteDailyWeeklyQuota(".runs/test_quota.sqlite")
    
    stop_is_set = stop_flag.is_stopped()
    quota_ok = quota.check_and_increment(1)
    
    observer.send_gate(
        stop=stop_is_set,
        quota_ok=quota_ok,
        seen_ok=True,  # Assume not seen
        mode="test",
        auto_send=True,
        remaining_quota=99
    )
    
    print(f"   Stop flag: {'❌ SET' if stop_is_set else '✅ clear'}")
    print(f"   Quota: {'✅ OK' if quota_ok else '❌ BLOCKED'}")
    
    if stop_is_set or not quota_ok:
        print("\n⚠️  Gates are blocking! Cannot proceed with send.")
        return
    
    # 6. Test the actual send pipeline
    test_message = f"""Hi! I noticed your profile and I'm really interested in your background.
I have experience in similar technologies and would love to connect to discuss potential collaboration.
Looking forward to hearing from you!
TEST MESSAGE {datetime.now().strftime('%H:%M:%S')}"""
    
    print(f"\n6. Testing send pipeline...")
    print(f"   Message preview: {test_message[:50]}...")
    
    # Create SendMessage use case
    send_message = SendMessage(
        browser=base_browser,
        logger=logger,
        stop=stop_flag,
        quota=quota
    )
    
    try:
        # Focus
        print("\n   a. Focusing message box...")
        browser.focus_message_box()
        time.sleep(0.5)
        
        # Fill
        print("   b. Filling message...")
        browser.fill_message(test_message)
        time.sleep(0.5)
        
        # Send
        print("   c. Clicking send...")
        browser.send()
        time.sleep(2)
        
        # Verify
        print("   d. Verifying sent...")
        sent_ok = browser.verify_sent()
        
        if sent_ok:
            observer.sent()
            print("\n   ✅ MESSAGE SENT SUCCESSFULLY!")
        else:
            print("\n   ❌ Verification failed - message may not have been sent")
        
    except Exception as e:
        print(f"\n   ❌ Error during send: {e}")
        import traceback
        traceback.print_exc()
    
    # 7. Analyze the pipeline
    print("\n7. Pipeline Analysis:")
    analyze_pipeline_log(".runs/auto_flow_test.jsonl")
    
    print("\n8. Browser will close in 5 seconds...")
    time.sleep(5)
    browser.close()

def analyze_pipeline_log(log_path: str):
    """Analyze the pipeline log to find issues."""
    log_file = Path(log_path)
    if not log_file.exists():
        print("   No log file found")
        return
    
    events = []
    with open(log_file) as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except:
                    pass
    
    if not events:
        print("   No events logged")
        return
    
    # Find the latest run
    latest_run = None
    for event in reversed(events):
        if "run_id" in event:
            latest_run = event["run_id"]
            break
    
    if not latest_run:
        print("   No run ID found")
        return
    
    run_events = [e for e in events if e.get("run_id") == latest_run]
    
    # Check pipeline stages
    stages = {
        "profile_extracted": "❌",
        "decision_request": "❌",
        "decision_response": "❌",
        "send_gate": "❌",
        "focus_message_box_result": "❌",
        "fill_message_result": "❌",
        "click_send_result": "❌",
        "verify_sent_attempt": "❌",
        "verify_sent_result": "❌",
        "sent": "❌"
    }
    
    for event in run_events:
        event_type = event.get("event")
        if event_type in stages:
            # Check if successful
            if event.get("ok") is False:
                stages[event_type] = "❌ FAILED"
            elif event.get("ok") is True:
                stages[event_type] = "✅"
            elif event_type in ["profile_extracted", "decision_request", "decision_response", "send_gate", "verify_sent_attempt", "sent"]:
                stages[event_type] = "✅"
    
    print("\n   Pipeline Status:")
    for stage, status in stages.items():
        print(f"   - {stage:30} {status}")
    
    # Find failures
    failures = []
    for event in run_events:
        if event.get("ok") is False:
            failures.append(event)
    
    if failures:
        print("\n   Failed Events:")
        for fail in failures:
            print(f"   - {fail.get('event')}: {fail.get('error', 'No error message')}")
            if fail.get("selector_used"):
                print(f"     Selector: {fail.get('selector_used')}")

if __name__ == "__main__":
    test_full_auto_flow()