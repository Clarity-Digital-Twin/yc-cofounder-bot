#!/usr/bin/env python
"""Test the full chain step by step."""

import os
from pathlib import Path

# Set up environment
os.environ["SHADOW_MODE"] = "1"  # Safe mode
os.environ["ENABLE_PLAYWRIGHT"] = "1"
os.environ["ENABLE_CUA"] = "0"  # No CUA for now
os.environ["DECISION_MODE"] = "rubric"  # Simple mode
os.environ["PACE_MIN_SECONDS"] = "0"  # No delays for testing

print("🧪 Testing Full Chain...")
print("=" * 50)

# Test 1: Import all modules
print("\n1️⃣ Testing imports...")
try:
    from yc_matcher.application.autonomous_flow import AutonomousFlow
    from yc_matcher.domain.entities import Criteria, Profile
    from yc_matcher.infrastructure.persistence.sqlite_quota import SQLiteDailyWeeklyQuota
    from yc_matcher.infrastructure.persistence.sqlite_repo import SQLiteSeenRepo
    from yc_matcher.infrastructure.control.stop_flag import FileStopFlag
    from yc_matcher.interface.di import build_services

    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)

# Test 2: Build services
print("\n2️⃣ Testing service building...")
try:
    eval_use, send_use, logger = build_services(
        criteria_text="Python, FastAPI",
        template_text="Hi {name}",
        decision_mode="rubric",
        threshold=4.0,
    )
    print("✅ Services built")
    print(f"   - Evaluator: {type(eval_use)}")
    print(f"   - Sender: {type(send_use)}")
    print(f"   - Logger: {type(logger)}")
    print(f"   - Browser: {type(send_use.browser)}")
except Exception as e:
    print(f"❌ Service building failed: {e}")
    exit(1)

# Test 3: Test evaluation
print("\n3️⃣ Testing evaluation...")
try:
    profile = Profile(raw_text="John Doe, Python developer")
    criteria = Criteria(text="Python")
    result = eval_use(profile, criteria)
    print("✅ Evaluation successful")
    print(f"   - Decision: {result.get('decision')}")
    print(f"   - Rationale: {result.get('rationale')}")
    print(f"   - Score: {result.get('score')}")
except Exception as e:
    print(f"❌ Evaluation failed: {e}")

# Test 4: Check browser type
print("\n4️⃣ Checking browser configuration...")
browser = send_use.browser
print(f"   - Browser type: {type(browser).__name__}")
print(f"   - Has open: {hasattr(browser, 'open')}")
print(f"   - Has click_view_profile: {hasattr(browser, 'click_view_profile')}")
print(f"   - Has read_profile_text: {hasattr(browser, 'read_profile_text')}")

# Test 5: Try to create autonomous flow
print("\n5️⃣ Testing autonomous flow creation...")
try:
    seen_repo = SQLiteSeenRepo(db_path=Path(".runs/seen.sqlite"))
    quota = SQLiteDailyWeeklyQuota(Path(".runs/quota.sqlite"))
    stop_flag = FileStopFlag(Path(".runs/stop.flag"))

    flow = AutonomousFlow(
        browser=send_use.browser,
        evaluate=eval_use,
        send=send_use,
        seen=seen_repo,
        logger=logger,
        stop=stop_flag,
        quota=quota,
    )
    print("✅ Autonomous flow created")
except Exception as e:
    print(f"❌ Flow creation failed: {e}")
    import traceback

    traceback.print_exc()

# Test 6: Check what browser we actually got
print("\n6️⃣ Browser diagnostics...")
if browser.__class__.__name__ == "_NullBrowser":
    print("⚠️  WARNING: Using NullBrowser (does nothing)")
    print("   Fix: Set ENABLE_PLAYWRIGHT=1 or ENABLE_CUA=1")
elif browser.__class__.__name__ == "PlaywrightBrowser":
    print("✅ Using PlaywrightBrowser")
    print("   This should open a real browser window")
elif browser.__class__.__name__ == "OpenAICUABrowser":
    print("✅ Using OpenAI CUA Browser")
    print("   This will use AI to control browser")
else:
    print(f"❓ Unknown browser type: {browser.__class__.__name__}")

print("\n" + "=" * 50)
print("🎯 Test Summary:")
if browser.__class__.__name__ == "_NullBrowser":
    print("❌ PROBLEM: Using NullBrowser - nothing will happen!")
    print("   Solution: Set ENABLE_PLAYWRIGHT=1 in environment")
else:
    print("✅ System should be functional!")
    print("   Browser will open when you click 'Start Autonomous Browsing'")
