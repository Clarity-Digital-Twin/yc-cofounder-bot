#!/usr/bin/env python
"""Test the full UI and browser integration."""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from yc_matcher.interface.di import build_services
from yc_matcher.application.autonomous_flow import AutonomousFlow
from yc_matcher.infrastructure.sqlite_repo import SQLiteSeenRepo
from yc_matcher.infrastructure.sqlite_quota import SQLiteDailyWeeklyQuota
from yc_matcher.infrastructure.stop_flag import FileStopFlag


def test_browser_login_flow():
    """Test browser login flow."""
    print("\n" + "="*60)
    print("TESTING BROWSER LOGIN FLOW")
    print("="*60)
    
    # Build minimal services just for browser
    eval_use, send_use, logger = build_services(
        criteria_text="Test criteria",
        template_text="Hi {name}",
        decision_mode="rubric",
        threshold=0.7,
    )
    
    browser = send_use.browser
    print(f"✅ Browser created: {type(browser).__name__}")
    
    # Open YC URL
    yc_url = os.getenv("YC_MATCH_URL", "https://www.startupschool.org/cofounder-matching")
    print(f"\nOpening: {yc_url}")
    browser.open(yc_url)
    print("✅ Browser opened YC Cofounder Matching")
    
    # Check login status
    time.sleep(2)  # Wait for page load
    is_logged = browser.is_logged_in()
    print(f"\nLogin status: {'✅ Logged in' if is_logged else '❌ Not logged in'}")
    
    if not is_logged:
        print("\n⚠️ Please log into YC in the browser window that opened")
        print("Waiting 20 seconds for manual login...")
        time.sleep(20)
        
        # Check again
        is_logged = browser.is_logged_in()
        print(f"Login status after wait: {'✅ Logged in' if is_logged else '❌ Still not logged in'}")
    
    return browser, is_logged


def test_profile_operations(browser):
    """Test profile reading and navigation."""
    print("\n" + "="*60)
    print("TESTING PROFILE OPERATIONS")
    print("="*60)
    
    try:
        # Try to click View Profile
        print("\nAttempting to click 'View Profile'...")
        clicked = browser.click_view_profile()
        
        if clicked:
            print("✅ Clicked View Profile button")
            
            # Wait for profile to load
            time.sleep(2)
            
            # Read profile text
            print("\nReading profile text...")
            profile_text = browser.read_profile_text()
            
            if profile_text:
                print(f"✅ Read profile ({len(profile_text)} chars)")
                print(f"Preview: {profile_text[:200]}...")
            else:
                print("❌ No profile text found")
                
            # Try to skip
            print("\nTrying to skip to next profile...")
            browser.skip()
            print("✅ Skipped to next profile")
            
        else:
            print("❌ Could not find View Profile button")
            print("   (User might not be logged in or no profiles available)")
            
    except Exception as e:
        print(f"❌ Error during profile operations: {e}")


def test_message_operations(browser):
    """Test message box operations."""
    print("\n" + "="*60)  
    print("TESTING MESSAGE OPERATIONS (SHADOW MODE)")
    print("="*60)
    
    try:
        # Focus message box
        print("\nFocusing message box...")
        browser.focus_message_box()
        print("✅ Focused message box")
        
        # Fill test message
        test_message = "TEST MESSAGE - SHADOW MODE - NOT SENDING"
        print(f"\nFilling message: '{test_message}'")
        browser.fill_message(test_message)
        print("✅ Filled message")
        
        # DON'T actually send in test mode
        print("\n⚠️ SHADOW MODE: Not sending message (safety)")
        
    except Exception as e:
        print(f"❌ Error during message operations: {e}")


def main():
    """Run all browser tests."""
    print("\n" + "="*70)
    print(" YC MATCHER - BROWSER INTEGRATION TEST")
    print("="*70)
    
    # Test 1: Browser and login
    browser, is_logged = test_browser_login_flow()
    
    if is_logged:
        # Test 2: Profile operations
        test_profile_operations(browser)
        
        # Test 3: Message operations (shadow mode)
        if os.getenv("SHADOW_MODE", "1") == "1":
            print("\n✅ SHADOW MODE is ON - safe to test message operations")
            test_message_operations(browser)
        else:
            print("\n⚠️ SHADOW MODE is OFF - skipping message test for safety")
    else:
        print("\n⚠️ Not logged in - skipping profile and message tests")
    
    print("\n" + "="*70)
    print(" TEST COMPLETE")
    print("="*70)
    
    # Keep browser open for 5 seconds to see results
    print("\nKeeping browser open for 5 seconds...")
    time.sleep(5)
    
    # Cleanup
    if hasattr(browser, 'cleanup'):
        browser.cleanup()
        print("✅ Browser cleaned up")


if __name__ == "__main__":
    main()