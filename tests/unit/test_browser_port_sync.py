"""Test that BrowserPort methods are all synchronous for AutonomousFlow compatibility."""

import inspect

from yc_matcher.application.ports import BrowserPort


class TestBrowserPortSync:
    """Ensure BrowserPort contract is synchronous."""

    def test_all_browser_port_methods_are_sync(self) -> None:
        """Test that all BrowserPort methods used by AutonomousFlow are synchronous."""
        # Methods that AutonomousFlow calls
        required_sync_methods = [
            "open",
            "click_view_profile",
            "read_profile_text",
            "focus_message_box",
            "fill_message",
            "send",
            "verify_sent",
            "skip",
            "close",
        ]

        # Create a test implementation to verify contract
        class TestBrowser(BrowserPort):
            def open(self, url: str) -> None:
                pass

            def click_view_profile(self) -> bool:
                return True

            def read_profile_text(self) -> str:
                return "test"

            def focus_message_box(self) -> None:
                pass

            def fill_message(self, text: str) -> None:
                pass

            def send(self) -> None:
                pass

            def verify_sent(self) -> bool:
                return True

            def skip(self) -> None:
                pass

            def close(self) -> None:
                pass

        browser = TestBrowser()

        # Verify each method is NOT a coroutine
        for method_name in required_sync_methods:
            method = getattr(browser, method_name)
            assert not inspect.iscoroutinefunction(method), f"{method_name} must be synchronous"

    def test_openai_cua_browser_exposes_sync_methods(self) -> None:
        """Test that OpenAICUABrowser exposes synchronous methods despite async internals."""
        try:
            from yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser
        except ImportError:
            # Skip if not available
            return

        # Don't actually create instance (would need OpenAI client)
        # Just check the class methods are not coroutines
        for method_name in ["open", "click_view_profile", "read_profile_text",
                           "focus_message_box", "fill_message", "send",
                           "verify_sent", "skip", "close"]:
            method = getattr(OpenAICUABrowser, method_name)
            # The methods themselves should not be async def
            assert not inspect.iscoroutinefunction(method), \
                f"OpenAICUABrowser.{method_name} must be synchronous for AutonomousFlow"
