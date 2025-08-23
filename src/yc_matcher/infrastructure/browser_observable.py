"""
Observable browser wrapper that adds pipeline tracing to any browser implementation.
"""

from typing import Any

from .send_pipeline_observer import SendPipelineObserver


class ObservableBrowser:
    """Wrapper that adds observability to browser operations."""

    def __init__(self, browser: Any, observer: SendPipelineObserver):
        self.browser = browser
        self.observer = observer
        self._last_selector = None
        self._last_button = None

    def open(self, url: str) -> bool:
        """Delegate to browser."""
        try:
            self.browser.open(url)
            return True
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False

    def click_view_profile(self) -> bool:
        """Delegate to browser."""
        return self.browser.click_view_profile()

    def read_profile_text(self) -> str:
        """Read and observe profile extraction."""
        text = self.browser.read_profile_text()
        if text:
            self.observer.profile_extracted(text)
        return text

    def focus_message_box(self) -> None:
        """Focus with observability."""
        selectors = [
            "textarea[placeholder*='message' i]",
            "[role='textbox']",
            "textarea",
            "[contenteditable='true']",
            "div[contenteditable='true']",
            "input[type='text'][placeholder*='message' i]"
        ]

        # Try with page directly if available
        if hasattr(self.browser, 'page') and self.browser.page:
            page = self.browser.page
            for selector in selectors:
                try:
                    elem = page.locator(selector).first
                    if elem.count() > 0:
                        elem.click()
                        self._last_selector = selector
                        self.observer.focus_message_box_result(
                            ok=True,
                            selector_used=selector
                        )
                        return
                except Exception:
                    continue

            # All failed
            self.observer.focus_message_box_result(
                ok=False,
                error="No selector matched"
            )
        else:
            # Fallback to browser's implementation
            try:
                self.browser.focus_message_box()
                self.observer.focus_message_box_result(ok=True)
            except Exception as e:
                self.observer.focus_message_box_result(
                    ok=False,
                    error=str(e)
                )

    def fill_message(self, text: str) -> None:
        """Fill with observability."""
        try:
            # If we have page and last selector, try that first
            if hasattr(self.browser, 'page') and self.browser.page and self._last_selector:
                page = self.browser.page
                elem = page.locator(self._last_selector).first

                if "contenteditable" in self._last_selector or "role='textbox'" in self._last_selector:
                    # Clear and type for contenteditable
                    page.keyboard.press("Control+a")
                    page.keyboard.type(text)
                else:
                    elem.fill(text)

                self.observer.fill_message_result(
                    ok=True,
                    chars=len(text),
                    selector_used=self._last_selector
                )
            else:
                # Use browser's implementation
                self.browser.fill_message(text)
                self.observer.fill_message_result(
                    ok=True,
                    chars=len(text)
                )
        except Exception as e:
            self.observer.fill_message_result(
                ok=False,
                chars=len(text),
                error=str(e)
            )
            raise

    def send(self) -> None:
        """Send with observability."""
        button_labels = [
            "Invite to connect",
            "Send invitation",
            "Connect",
            "Send",
            "Submit"
        ]

        if hasattr(self.browser, 'page') and self.browser.page:
            page = self.browser.page
            for label in button_labels:
                try:
                    # Try exact match
                    btn = page.get_by_role("button", name=label)
                    if btn.count() > 0:
                        btn.first.click()
                        self._last_button = label
                        self.observer.click_send_result(
                            ok=True,
                            button_variant=label
                        )
                        return

                    # Try partial match
                    btn = page.locator(f"button:has-text('{label}')")
                    if btn.count() > 0:
                        btn.first.click()
                        self._last_button = label
                        self.observer.click_send_result(
                            ok=True,
                            button_variant=f"{label} (partial)"
                        )
                        return
                except Exception:
                    continue

            # No button found
            self.observer.click_send_result(
                ok=False,
                error="No send button found"
            )
        else:
            # Fallback
            try:
                self.browser.send()
                self.observer.click_send_result(ok=True)
            except Exception as e:
                self.observer.click_send_result(
                    ok=False,
                    error=str(e)
                )
                raise

    def verify_sent(self) -> bool:
        """Verify with observability."""
        checks = [
            "text=/sent|delivered/i",
            "text=/invitation sent/i",
            ".toast-success",
            "[role='alert']",
            "textarea:empty"
        ]

        self.observer.verify_sent_attempt(checks)

        if hasattr(self.browser, 'page') and self.browser.page:
            page = self.browser.page
            counts = {}

            for check in checks:
                try:
                    if check.startswith("text="):
                        pattern = check[5:]
                        count = page.locator(f"text={pattern}").count()
                    elif check == "textarea:empty":
                        elem = page.locator("textarea").first
                        if elem.count() > 0:
                            val = elem.input_value()
                            count = 1 if val == "" else 0
                        else:
                            count = 0
                    else:
                        count = page.locator(check).count()

                    counts[check] = count

                    if count > 0:
                        self.observer.verify_sent_result(
                            ok=True,
                            matched_selector=check,
                            counts=counts
                        )
                        return True
                except Exception:
                    counts[check] = 0

            # Nothing matched
            self.observer.verify_sent_result(
                ok=False,
                counts=counts
            )
            return False
        else:
            # Fallback
            result = self.browser.verify_sent()
            self.observer.verify_sent_result(ok=result)
            return result

    def skip(self) -> None:
        """Delegate to browser."""
        self.browser.skip()

    def close(self) -> None:
        """Delegate to browser."""
        if hasattr(self.browser, 'close'):
            self.browser.close()
