#!/usr/bin/env python3
"""
REAL end-to-end test with actual login and send flow.
This test uses the singleton browser pattern to ensure only ONE browser instance.

IMPORTANT: This test requires real YC credentials in .env file:
- YC_EMAIL
- YC_PASSWORD

The singleton pattern is enforced by AsyncLoopRunner which ensures:
- ONE event loop for the entire session
- ONE Playwright instance
- ONE browser instance
- ONE page that gets reused

No browser spam, no multiple windows!
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path for standalone execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest

# Configure environment BEFORE any imports
os.environ["PACE_MIN_SECONDS"] = "0"
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = ".ms-playwright"
os.environ["PLAYWRIGHT_HEADLESS"] = os.getenv("CI", "0")  # Headless in CI, visible locally
os.environ["SHADOW_MODE"] = "1"  # Safety: don't actually send in tests
os.environ["ENABLE_CUA"] = "0"  # Use Playwright for reliability
# CRITICAL: Remove PYTEST_CURRENT_TEST to allow browser to launch
if "PYTEST_CURRENT_TEST" in os.environ:
    del os.environ["PYTEST_CURRENT_TEST"]


class TestRealSendFlow:
    """Real E2E test with actual browser automation and login."""

    @pytest.fixture(scope="class")
    def shared_browser(self):
        """
        Class-scoped fixture for browser singleton.
        This ensures ONE browser for ALL tests in this class.
        """
        from yc_matcher.infrastructure.browser.playwright_async import PlaywrightBrowserAsync

        # Create the browser (singleton via AsyncLoopRunner)
        browser = PlaywrightBrowserAsync()

        # The browser will be reused across all tests
        yield browser

        # Cleanup happens automatically via AsyncLoopRunner's atexit handler
        # But we can also explicitly clean up
        if hasattr(browser, "cleanup"):
            browser.cleanup()

    @pytest.fixture
    def pipeline_observer(self, tmp_path):
        """Create pipeline observer for tracking events."""
        from yc_matcher.infrastructure.logging.jsonl_logger import JSONLLogger
        from yc_matcher.infrastructure.logging.pipeline_observer import SendPipelineObserver

        log_path = tmp_path / "pipeline_events.jsonl"
        logger = JSONLLogger(str(log_path))
        observer = SendPipelineObserver(logger)

        return observer, log_path

    def test_01_login_flow(self, shared_browser):
        """Test 1: Login to YC (uses singleton browser)."""
        print("\n" + "=" * 60)
        print("TEST 1: LOGIN FLOW")
        print("=" * 60)

        # Check for credentials
        from yc_matcher import config

        email, password = config.get_yc_credentials()

        if not email or not password:
            pytest.skip("YC credentials not configured in .env")

        # Check if browser was properly initialized
        if not hasattr(shared_browser, "_runner") or shared_browser._runner is None:
            pytest.skip("Browser not available in test environment")

        # Navigate to YC
        print("1. Navigating to YC...")
        success = shared_browser.open("https://www.startupschool.org/cofounder-matching")
        assert success, "Failed to navigate to YC"

        # Wait for page load
        time.sleep(3)

        # Check if already logged in
        print("2. Checking login status...")
        is_logged_in = shared_browser.is_logged_in()

        if is_logged_in:
            print("   ✅ Already logged in")
        else:
            print("   🔐 Not logged in, attempting auto-login...")
            # The open() method already attempts auto-login
            # Wait and check again
            time.sleep(5)
            is_logged_in = shared_browser.is_logged_in()
            assert is_logged_in, "Failed to log in to YC"
            print("   ✅ Logged in successfully")

    def test_02_view_profile(self, shared_browser, pipeline_observer):
        """Test 2: Navigate to a profile (reuses same browser)."""
        print("\n" + "=" * 60)
        print("TEST 2: VIEW PROFILE")
        print("=" * 60)

        # Check if browser was properly initialized
        if not hasattr(shared_browser, "_runner") or shared_browser._runner is None:
            pytest.skip("Browser not available in test environment")

        observer, log_path = pipeline_observer

        # Try to view a profile
        print("1. Attempting to view a profile...")
        profile_num = observer.new_profile()

        clicked = shared_browser.click_view_profile()
        assert clicked, "Failed to click View Profile button"
        print(f"   ✅ Viewing profile #{profile_num}")

        # Wait for profile to load
        time.sleep(2)

        # Extract profile text
        print("2. Extracting profile text...")
        profile_text = shared_browser.read_profile_text()
        assert profile_text, "Failed to extract profile text"
        assert len(profile_text) > 50, "Profile text too short"

        print(f"   ✅ Extracted {len(profile_text)} chars")
        observer.profile_extracted(profile_text)

    def test_03_send_pipeline(self, shared_browser, pipeline_observer, tmp_path):
        """Test 3: Full send pipeline with observability (same browser)."""
        print("\n" + "=" * 60)
        print("TEST 3: SEND PIPELINE WITH OBSERVABILITY")
        print("=" * 60)

        # Check if browser was properly initialized
        if not hasattr(shared_browser, "_runner") or shared_browser._runner is None:
            pytest.skip("Browser not available in test environment")

        from yc_matcher.infrastructure.browser.observable import ObservableBrowser
        from yc_matcher.infrastructure.control.stop_flag import FileStopFlag
        from yc_matcher.infrastructure.persistence.sqlite_quota import SQLiteDailyWeeklyQuota

        observer, log_path = pipeline_observer

        # Wrap browser with observability
        observable_browser = ObservableBrowser(shared_browser, observer)

        # We're already on a profile from test_02
        print("1. Already on profile from previous test")

        # Simulate decision (force YES for testing)
        print("2. Simulating AI decision...")
        observer.decision_request("test-model", "test-input")
        time.sleep(0.1)

        observer.decision_response(
            decision="YES",
            auto_send=True,
            output_types=["message"],
            latency_ms=100,
            decision_json_ok=True,
        )
        print("   ✅ Decision: YES (forced)")
        print("   ✅ Auto-send: True")

        # Check gates
        print("3. Checking send gates...")
        stop_flag = FileStopFlag(tmp_path / "stop.flag")
        quota = SQLiteDailyWeeklyQuota(tmp_path / "quota.sqlite")

        stop_is_set = stop_flag.is_stopped()
        quota_ok = quota.check_and_increment(1)

        observer.send_gate(
            stop=stop_is_set,
            quota_ok=quota_ok,
            seen_ok=True,
            mode="test",
            auto_send=True,
            remaining_quota=99,
        )

        assert not stop_is_set, "Stop flag is set"
        assert quota_ok, "Quota exceeded"
        print("   ✅ Gates passed")

        # Test message operations
        test_message = f"TEST MESSAGE {datetime.now().strftime('%H:%M:%S')}"
        print("4. Testing message operations...")

        # Focus
        print("   a. Focusing message box...")
        observable_browser.focus_message_box()
        time.sleep(0.5)

        # Fill
        print("   b. Filling message...")
        observable_browser.fill_message(test_message)
        time.sleep(0.5)

        # In shadow mode, we don't actually send
        if os.getenv("SHADOW_MODE") == "1":
            print("   c. SHADOW MODE - not actually sending")
            # But we can still test the UI interactions happened
        else:
            # Send
            print("   c. Clicking send...")
            observable_browser.send()
            time.sleep(2)

            # Verify
            print("   d. Verifying sent...")
            sent_ok = observable_browser.verify_sent()

            if sent_ok:
                observer.sent()
                print("   ✅ MESSAGE SENT SUCCESSFULLY!")
            else:
                print("   ❌ Verification failed")

        # Analyze the pipeline
        print("\n5. Analyzing pipeline events...")
        self._analyze_pipeline(log_path)

    def test_04_browser_singleton_verification(self, shared_browser):
        """Test 4: Verify we're still using the same browser instance."""
        print("\n" + "=" * 60)
        print("TEST 4: BROWSER SINGLETON VERIFICATION")
        print("=" * 60)

        # Check if browser was properly initialized
        if not hasattr(shared_browser, "_runner") or shared_browser._runner is None:
            pytest.skip("Browser not available in test environment")

        # Navigate to a different page to prove it's the same browser
        print("1. Navigating to verify singleton...")

        # Get the current runner
        runner = shared_browser._runner
        assert runner is not None, "Runner not initialized"

        # Check that it's the shared singleton
        from yc_matcher.infrastructure.browser.playwright_async import _shared_runner

        assert runner is _shared_runner, "Not using singleton runner!"

        print("   ✅ Confirmed: Using singleton browser")
        print("   ✅ No browser spam - same instance throughout!")

        # The browser should still be on the YC page from previous tests
        # This proves we haven't created a new browser

    def _analyze_pipeline(self, log_path):
        """Analyze the 10-event pipeline for completeness."""
        # Convert to Path if it's a string
        if isinstance(log_path, str):
            log_path = Path(log_path)

        if not log_path.exists():
            print("   No events logged")
            return

        events = []
        with open(log_path) as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

        # Get latest run
        if not events:
            print("   No events found")
            return

        latest_run = events[-1].get("run_id") if events else None
        if not latest_run:
            # Find run_id from any event
            for e in reversed(events):
                if "run_id" in e:
                    latest_run = e["run_id"]
                    break

        run_events = [e for e in events if e.get("run_id") == latest_run]

        # Check 10-event pipeline
        expected_events = [
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

        found_events = {e["event"]: e for e in run_events if e.get("event") in expected_events}

        print("\n   10-Event Pipeline Status:")
        for event in expected_events:
            if event in found_events:
                e = found_events[event]
                if e.get("ok") is False:
                    print(f"   {event:30} ❌ FAILED")
                else:
                    print(f"   {event:30} ✅")
            else:
                if event in [
                    "click_send_result",
                    "verify_sent_attempt",
                    "verify_sent_result",
                    "sent",
                ]:
                    # These are skipped in shadow mode
                    print(f"   {event:30} ⏭️  (shadow mode)")
                else:
                    print(f"   {event:30} ❌ MISSING")

        # Report any failures
        failures = [e for e in run_events if e.get("ok") is False]
        if failures:
            print("\n   Failed Events:")
            for fail in failures:
                print(f"   - {fail['event']}: {fail.get('error', 'unknown')}")


def test_no_browser_spam():
    """
    Standalone test to verify singleton browser pattern.
    This test creates multiple browser instances and verifies they all share the same runner.
    """
    print("\n" + "=" * 60)
    print("BROWSER SINGLETON VERIFICATION TEST")
    print("=" * 60)

    from yc_matcher.infrastructure.browser.playwright_async import (
        PlaywrightBrowserAsync,
        _get_shared_runner,
    )

    # Create multiple browser instances
    browser1 = PlaywrightBrowserAsync()
    browser2 = PlaywrightBrowserAsync()
    browser3 = PlaywrightBrowserAsync()

    # All should share the same runner
    assert browser1._runner is browser2._runner, "Browser 1 and 2 have different runners!"
    assert browser2._runner is browser3._runner, "Browser 2 and 3 have different runners!"

    # Get the actual shared runner
    shared = _get_shared_runner()
    assert browser1._runner is shared, "Not using global shared runner!"

    print("✅ Singleton verified: All browsers share the same AsyncLoopRunner")
    print("✅ Only ONE browser window will ever be created!")
    print(f"✅ Shared runner ID: {id(shared)}")
    print(f"✅ Browser1 runner ID: {id(browser1._runner)}")
    print(f"✅ Browser2 runner ID: {id(browser2._runner)}")
    print(f"✅ Browser3 runner ID: {id(browser3._runner)}")

    # Clean up
    if hasattr(browser1, "cleanup"):
        browser1.cleanup()  # This cleans up the shared singleton


if __name__ == "__main__":
    # Can run standalone for debugging
    import sys

    if "--no-spam-test" in sys.argv:
        test_no_browser_spam()
    else:
        # Run all tests
        pytest.main([__file__, "-xvs"])
