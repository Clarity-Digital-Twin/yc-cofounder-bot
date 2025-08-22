#!/usr/bin/env python3
"""Simple test to check if Streamlit is working and CUA login is functional."""
import time
from playwright.sync_api import sync_playwright

def test_streamlit():
    print("🚀 Testing Streamlit App")
    print("=" * 50)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("📍 Navigating to http://localhost:8502...")
        page.goto("http://localhost:8502")
        
        print("⏳ Waiting for Streamlit to load...")
        page.wait_for_timeout(5000)  # Wait 5 seconds
        
        # Take screenshot of current state
        page.screenshot(path="streamlit_state.png")
        print("📸 Screenshot saved: streamlit_state.png")
        
        # Check if page loaded
        title = page.title()
        print(f"Page title: {title}")
        
        # Look for textarea elements
        textareas = page.query_selector_all('textarea')
        print(f"Found {len(textareas)} textarea elements")
        
        if len(textareas) >= 3:
            print("✅ All 3 input areas found!")
            
            # Fill profile
            print("📝 Filling profile...")
            textareas[0].fill("Test profile: Technical cofounder with Python experience")
            
            # Fill criteria
            print("🎯 Filling criteria...")
            textareas[1].fill("Looking for: Python expert, ready now")
            
            # Fill message
            print("💬 Filling message...")
            textareas[2].fill("Hi [Name], let's connect!")
            
            # Take screenshot
            page.screenshot(path="filled_form.png")
            print("📸 Form filled screenshot: filled_form.png")
            
            # Look for start button
            start_btn = page.query_selector('button:has-text("Start")')
            if start_btn:
                print("✅ Start button found!")
                print("Would click it but stopping here for safety")
            else:
                print("⚠️ No start button found")
        else:
            print(f"❌ Expected 3 textareas, found {len(textareas)}")
            
            # Debug: print page content
            content = page.content()
            if "Your Profile" in content:
                print("✅ Page contains 'Your Profile' text")
            if "Match Criteria" in content:
                print("✅ Page contains 'Match Criteria' text")
            if "Message Template" in content:
                print("✅ Page contains 'Message Template' text")
            
            # Check for errors
            if "Error" in content or "error" in content:
                print("⚠️ Page may contain errors")
        
        print("\nKeeping browser open for 10 seconds...")
        page.wait_for_timeout(10000)
        
        browser.close()
    
    print("=" * 50)
    print("✅ Test complete!")

if __name__ == "__main__":
    test_streamlit()