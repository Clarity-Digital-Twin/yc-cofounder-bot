"""Test that browser singleton prevents multiple browser instances."""

import os
import time
from unittest.mock import Mock, patch

# Set test environment
os.environ["CUA_MODEL"] = "test-model"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["PLAYWRIGHT_HEADLESS"] = "1"  # Headless for tests


class TestBrowserSingleton:
    """Test browser lifecycle management."""
    
    def test_single_browser_across_multiple_calls(self) -> None:
        """Test that only ONE browser is created across multiple method calls."""
        # Track browser launches
        browser_launches = []
        
        with patch("playwright.async_api.async_playwright") as mock_playwright:
            # Mock playwright setup
            mock_pw_instance = Mock()
            mock_browser = Mock()
            mock_browser.is_connected.return_value = True
            mock_page = Mock()
            
            # Track launches
            def track_launch(*args, **kwargs):
                browser_launches.append(time.time())
                return mock_browser
                
            mock_pw_instance.chromium.launch = Mock(side_effect=track_launch)
            mock_browser.new_page = Mock(return_value=mock_page)
            
            # Mock async context manager
            async def async_start():
                return mock_pw_instance
                
            mock_playwright.return_value.start = Mock(side_effect=async_start)
            
            # Mock OpenAI client
            with patch("openai.OpenAI") as mock_openai:
                mock_client = Mock()
                mock_response = Mock()
                mock_response.id = "test-id"
                mock_response.output = []
                mock_client.responses.create = Mock(return_value=mock_response)
                mock_openai.return_value = mock_client
                
                # Import AFTER mocks are set up
                from yc_matcher.infrastructure.openai_cua_browser_professional import (
                    OpenAICUABrowserProfessional
                )
                
                # Create browser instance
                browser = OpenAICUABrowserProfessional()
                
                # Make multiple calls that would previously create multiple browsers
                browser.open("https://example.com")
                browser.click_view_profile()
                browser.read_profile_text()
                browser.focus_message_box()
                browser.fill_message("test")
                browser.send()
                browser.verify_sent()
                browser.skip()
                
                # Assert only ONE browser was launched
                assert len(browser_launches) <= 1, \
                    f"Expected 1 browser launch, got {len(browser_launches)}"
                    
    def test_browser_manager_is_singleton(self) -> None:
        """Test that BrowserManager follows singleton pattern."""
        from yc_matcher.infrastructure.browser_singleton import BrowserManager
        
        # Create multiple instances
        manager1 = BrowserManager()
        manager2 = BrowserManager()
        manager3 = BrowserManager()
        
        # All should be the same instance
        assert manager1 is manager2
        assert manager2 is manager3
        assert id(manager1) == id(manager2) == id(manager3)
        
    def test_browser_survives_across_cua_instances(self) -> None:
        """Test browser persists even if CUA browser is recreated."""
        with patch("playwright.async_api.async_playwright"):
            with patch("openai.OpenAI"):
                from yc_matcher.infrastructure.browser_singleton import BrowserManager
                from yc_matcher.infrastructure.openai_cua_browser_professional import (
                    OpenAICUABrowserProfessional
                )
                
                # Get manager before creating CUA browsers
                manager_before = BrowserManager()
                
                # Create and destroy multiple CUA browser instances
                cua1 = OpenAICUABrowserProfessional()
                del cua1
                
                cua2 = OpenAICUABrowserProfessional()
                del cua2
                
                # Manager should still be the same instance
                manager_after = BrowserManager()
                assert manager_before is manager_after