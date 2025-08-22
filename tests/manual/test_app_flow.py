#!/usr/bin/env python
"""Test the YC Matcher application flow end-to-end."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from yc_matcher.application.autonomous_flow import AutonomousFlow
from yc_matcher.infrastructure.sqlite_quota import SQLiteDailyWeeklyQuota
from yc_matcher.infrastructure.sqlite_repo import SQLiteSeenRepo
from yc_matcher.infrastructure.stop_flag import FileStopFlag
from yc_matcher.interface.di import build_services


async def test_flow():
    """Test the complete application flow."""

    # Sample inputs (same as in the UI)
    your_profile = """
    Hey I'm Dr. Jung, a psychiatrist and builder. 
    I'm currently shipping Brain Go Brrr: a clinical-grade EEG analysis platform.
    """

    criteria_text = """
    Stack fit: Python + PyTorch, FastAPI, Docker/K8s, CI/CD, AWS/GCP/Azure.
    Health/regulated: EHR/HL7/FHIR, HIPAA, EMR integration.
    """

    template_text = """
    Hey {name},
    Your {project} shows the skills I need. 
    I'm John, shipping clinical AI. Quick call?
    """

    print("Building services...")

    # Build services
    eval_use, send_use, logger = build_services(
        criteria_text=criteria_text,
        template_text=template_text,
        decision_mode="hybrid",
        threshold=0.72,
    )

    print(f"Browser type: {type(send_use.browser).__name__}")

    # Create dependencies
    seen_repo = SQLiteSeenRepo(db_path=Path(".runs/seen.sqlite"))
    quota = SQLiteDailyWeeklyQuota(Path(".runs/quota.sqlite"))
    stop_flag = FileStopFlag(Path(".runs/stop.flag"))

    # Create autonomous flow
    flow = AutonomousFlow(
        browser=send_use.browser,
        evaluate=eval_use,
        send=send_use,
        seen=seen_repo,
        logger=logger,
        stop=stop_flag,
        quota=quota,
    )

    print("Testing browser operations...")

    # Test opening browser
    try:
        yc_url = os.getenv("YC_MATCH_URL", "https://www.startupschool.org/cofounder-matching")
        print(f"Opening: {yc_url}")

        # Open browser to YC
        send_use.browser.open(yc_url)
        print("✅ Browser opened successfully")

        # Wait a bit to see the page
        await asyncio.sleep(3)

        print("\nWould run autonomous flow, but stopping here for safety")
        print("(Set SHADOW_MODE=0 and remove this check to actually send)")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\nTest complete!")


if __name__ == "__main__":
    asyncio.run(test_flow())
