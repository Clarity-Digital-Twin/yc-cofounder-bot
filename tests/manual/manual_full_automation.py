#!/usr/bin/env python
"""Test FULL automation including auto-login."""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

# Ensure credentials are loaded
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("🚀 FULL AUTOMATION TEST - WITH AUTO-LOGIN")
print("=" * 70)

# Check credentials
email = os.getenv("YC_EMAIL")
password = os.getenv("YC_PASSWORD")

if email and password:
    print("\n✅ Credentials found:")
    print(f"   Email: {email}")
    print(f"   Password: {'*' * len(password)}")
else:
    print("\n⚠️ No credentials in .env - will need manual login")

from yc_matcher.application.autonomous_flow import AutonomousFlow
from yc_matcher.infrastructure.sqlite_quota import SQLiteDailyWeeklyQuota
from yc_matcher.infrastructure.sqlite_repo import SQLiteSeenRepo
from yc_matcher.infrastructure.stop_flag import FileStopFlag
from yc_matcher.interface.di import build_services

# Build services
print("\n1️⃣ Building services...")
eval_use, send_use, logger = build_services(
    criteria_text="Python, ML, Healthcare",
    template_text="Hi {name}, let's connect!",
    decision_mode="hybrid",
    threshold=0.7,
)

browser = send_use.browser
print(f"   Browser type: {type(browser).__name__}")

# Open YC and auto-login
print("\n2️⃣ Opening YC Cofounder Matching...")
yc_url = os.getenv("YC_MATCH_URL", "https://www.startupschool.org/cofounder-matching")
browser.open(yc_url)

# Wait for auto-login
print("\n3️⃣ Waiting for auto-login to complete...")
time.sleep(5)

# Check if logged in
is_logged = browser.is_logged_in()
print(f"\n4️⃣ Login status: {'✅ LOGGED IN!' if is_logged else '❌ Not logged in'}")

if is_logged:
    # Try to click view profile
    print("\n5️⃣ Testing profile navigation...")
    clicked = browser.click_view_profile()

    if clicked:
        print("   ✅ Found and clicked 'View Profile' button")

        # Read profile
        time.sleep(2)
        profile_text = browser.read_profile_text()
        if profile_text:
            print(f"   ✅ Read profile text ({len(profile_text)} chars)")
            print(f"   Preview: {profile_text[:100]}...")

        # Test skip
        browser.skip()
        print("   ✅ Skipped to next profile")
    else:
        print("   ⚠️ No 'View Profile' button found")
        print("   This might mean:")
        print("   - No profiles available")
        print("   - Different page layout")
        print("   - Need to navigate to correct section")

    # Create full flow
    print("\n6️⃣ Testing autonomous flow...")
    seen_repo = SQLiteSeenRepo(db_path=Path(".runs/seen.sqlite"))
    quota = SQLiteDailyWeeklyQuota(Path(".runs/quota.sqlite"))
    stop_flag = FileStopFlag(Path(".runs/stop.flag"))

    flow = AutonomousFlow(
        browser=browser,
        evaluate=eval_use,
        send=send_use,
        seen=seen_repo,
        logger=logger,
        stop=stop_flag,
        quota=quota,
    )

    print("   Running autonomous flow (shadow mode)...")
    results = flow.run(
        your_profile="Test profile",
        criteria="Python, ML",
        template="Hi {name}",
        mode="hybrid",
        limit=2,
        shadow_mode=True,  # Safety
        threshold=0.7,
        alpha=0.5,
    )

    print("\n   Results:")
    print(f"   • Evaluated: {results['total_evaluated']}")
    print(f"   • Sent: {results['total_sent']}")
    print(f"   • Skipped: {results['total_skipped']}")

else:
    print("\n⚠️ Auto-login failed. Please check:")
    print("   1. Credentials are correct in .env")
    print("   2. YC login page structure hasn't changed")
    print("   3. Network is working")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)

# Keep browser open
print("\nKeeping browser open for 10 seconds...")
time.sleep(10)
