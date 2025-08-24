#!/usr/bin/env python
"""Final comprehensive test of the YC Matcher application."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment for Playwright
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = ".ms-playwright"
os.environ["ENABLE_PLAYWRIGHT"] = "1"
os.environ["ENABLE_CUA"] = "0"
os.environ["PLAYWRIGHT_HEADLESS"] = "0"  # Visible browser

from yc_matcher.application.autonomous_flow import AutonomousFlow
from yc_matcher.infrastructure.persistence.sqlite_quota import SQLiteDailyWeeklyQuota
from yc_matcher.infrastructure.persistence.sqlite_repo import SQLiteSeenRepo
from yc_matcher.infrastructure.control.stop_flag import FileStopFlag
from yc_matcher.interface.di import build_services

# Sample inputs matching the UI
your_profile = """
Hey I'm Dr. Jung, a psychiatrist and builder. I'm currently shipping Brain Go Brrr:
a clinical-grade EEG analysis platform for neurologists and psychiatrists.
"""

criteria_text = """
Stack fit: Python + PyTorch, FastAPI, Docker/K8s, CI/CD, AWS/GCP/Azure.
Signal processing/time-series: EEG/BCI, scipy.signal, MNE, streaming, CUDA/GPU inference.
Health/regulated: EHR/HL7/FHIR, HIPAA, EMR integration, clinician-in-the-loop UX.
"""

template_text = """
Hey {name},

Your {project} shows the {skills} I need. I'm John, a psychiatrist shipping an open clinical AI prototype.

Quick call?
"""

# Settings
mode = "hybrid"
max_profiles = 2  # Small number for testing
shadow_mode = True  # Safety mode
threshold = 0.72
alpha = 0.50

print("=" * 70)
print("🚀 YC MATCHER - COMPREHENSIVE APPLICATION TEST")
print("=" * 70)

print(f"""
📋 Configuration:
- Decision Mode: {mode}
- Max Profiles: {max_profiles}
- Shadow Mode: {shadow_mode} (SAFE - no messages will be sent)
- Threshold: {threshold}
- Alpha: {alpha}
- Browser: Visible (PLAYWRIGHT_HEADLESS=0)
""")

try:
    print("1️⃣ Building services...")
    # Build services exactly as UI does
    eval_use, send_use, logger = build_services(
        criteria_text=criteria_text,
        template_text=template_text,
        prompt_ver="v1",
        rubric_ver="v1",
        decision_mode=mode,
        threshold=threshold,
    )

    print("   ✅ Services built successfully")
    print(f"   • Browser: {type(send_use.browser).__name__}")
    print(f"   • Logger: {type(logger).__name__}")
    print(f"   • Evaluator: {type(eval_use).__name__}")

    # Create dependencies
    print("\n2️⃣ Creating flow dependencies...")
    seen_repo = SQLiteSeenRepo(db_path=Path(".runs/seen.sqlite"))
    quota = SQLiteDailyWeeklyQuota(Path(".runs/quota.sqlite"))
    stop_flag = FileStopFlag(Path(".runs/stop.flag"))
    print("   ✅ Dependencies created")

    # Create autonomous flow
    print("\n3️⃣ Creating autonomous flow orchestrator...")
    flow = AutonomousFlow(
        browser=send_use.browser,
        evaluate=eval_use,
        send=send_use,
        seen=seen_repo,
        logger=logger,
        stop=stop_flag,
        quota=quota,
    )
    print("   ✅ Autonomous flow created")

    # Test browser operations
    print("\n4️⃣ Testing browser operations...")
    yc_url = os.getenv("YC_MATCH_URL", "https://www.startupschool.org/cofounder-matching")
    print(f"   Opening: {yc_url}")
    send_use.browser.open(yc_url)
    print("   ✅ Browser opened successfully")

    # Check login status
    print("\n5️⃣ Checking login status...")
    is_logged = send_use.browser.is_logged_in()
    if is_logged:
        print("   ✅ Already logged into YC")
    else:
        print("   ⚠️ Not logged in - please log in manually in the browser")
        print("   Waiting 15 seconds for manual login...")
        import time

        time.sleep(15)
        is_logged = send_use.browser.is_logged_in()
        if is_logged:
            print("   ✅ Now logged in!")
        else:
            print("   ❌ Still not logged in")

    if is_logged:
        # Execute autonomous flow
        print("\n6️⃣ Starting autonomous flow...")
        print("   This will evaluate profiles based on your criteria")
        print(f"   Shadow Mode: {shadow_mode} - NO messages will be sent")

        results = flow.run(
            your_profile=your_profile,
            criteria=criteria_text,
            template=template_text,
            mode=mode,
            limit=max_profiles,
            shadow_mode=shadow_mode,
            threshold=threshold,
            alpha=alpha,
        )

        print("\n✅ AUTONOMOUS FLOW COMPLETED!")
        print("\n📊 Results Summary:")
        print(f"   • Total Evaluated: {results['total_evaluated']}")
        print(f"   • Total Sent: {results['total_sent']}")
        print(f"   • Total Skipped: {results['total_skipped']}")

        if results.get("results"):
            print("\n📋 Detailed Results:")
            for i, result in enumerate(results["results"], 1):
                print(f"\n   Profile {i}:")
                print(f"   • Decision: {result.get('decision', 'N/A')}")
                print(f"   • Score: {result.get('score', 'N/A')}")
                if result.get("rationale"):
                    print(f"   • Rationale: {result['rationale'][:100]}...")
    else:
        print("\n⚠️ Cannot run autonomous flow without login")
        print("   Please run the test again and log in when the browser opens")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback

    print("\nFull traceback:")
    traceback.print_exc()

print("\n" + "=" * 70)
print("🎉 TEST COMPLETE")
print("=" * 70)
print("\n💡 Next Steps:")
print("1. If not logged in, run the test again and log in manually")
print("2. To run with real sending, set SHADOW_MODE=0 in .env")
print("3. To use the UI, go to http://localhost:8502")
print("4. To stop the app, press Ctrl+C or run: pkill -f streamlit")
