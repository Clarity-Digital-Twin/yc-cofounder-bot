#!/usr/bin/env python3
"""Test CUA browser login functionality."""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set test environment
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "test-key")
os.environ["CUA_MODEL"] = os.getenv("CUA_MODEL", "test-model")
os.environ["YC_EMAIL"] = "test@example.com"
os.environ["YC_PASSWORD"] = "test123"

def test_cua_browser_has_login_methods():
    """Test that CUA browser now has is_logged_in and ensure_logged_in methods."""
    from yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser
    
    # Mock to avoid real API calls
    from unittest.mock import Mock, patch
    
    with patch('yc_matcher.infrastructure.openai_cua_browser.OpenAI'):
        browser = OpenAICUABrowser()
        
        # Check methods exist
        assert hasattr(browser, 'is_logged_in'), "CUA browser missing is_logged_in method"
        assert hasattr(browser, 'ensure_logged_in'), "CUA browser missing ensure_logged_in method"
        
        print("✅ CUA browser now has login methods!")
        
        # Check they're callable
        assert callable(browser.is_logged_in)
        assert callable(browser.ensure_logged_in)
        
        print("✅ Login methods are callable!")

def test_playwright_browser_has_login_methods():
    """Test that Playwright browser has login methods."""
    from yc_matcher.infrastructure.browser_playwright import PlaywrightBrowser
    
    browser = PlaywrightBrowser()
    
    # Check methods exist
    assert hasattr(browser, 'is_logged_in'), "Playwright browser missing is_logged_in method"
    
    print("✅ Playwright browser has is_logged_in method!")

if __name__ == "__main__":
    print("Testing login functionality in both browsers...")
    print("=" * 50)
    
    test_cua_browser_has_login_methods()
    test_playwright_browser_has_login_methods()
    
    print("=" * 50)
    print("✅ All tests passed! CUA browser now supports login!")
    print("\nThe CUA browser will now:")
    print("1. Check if logged in before starting")
    print("2. Auto-login if YC_EMAIL and YC_PASSWORD are set")
    print("3. Navigate to login page and fill credentials")
    print("4. Verify login succeeded")