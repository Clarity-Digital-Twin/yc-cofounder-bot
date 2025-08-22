from __future__ import annotations

import os
from collections.abc import Iterable

try:
    from playwright.sync_api import Page, sync_playwright
except Exception:  # pragma: no cover

    class _Stub:  # minimal stub types to satisfy annotations
        pass

    Page = _Stub
    sync_playwright = None


class PlaywrightBrowser:
    """Sync Playwright adapter that approximates BrowserPort.

    Uses the sync API to match our sync BrowserPort methods.
    """

    def __init__(self) -> None:
        self._page: Page | None = None
        self._pl = None

    def _ensure_page(self) -> Page:
        if self._page is not None:
            return self._page
        if sync_playwright is None:  # pragma: no cover
            raise RuntimeError(
                "Playwright not available; install with `python -m playwright install chromium`"
            )
        pl = sync_playwright()
        self._pl = pl
        # Default to VISIBLE browser for YC login flow
        headless = os.getenv("PLAYWRIGHT_HEADLESS", "0") in {"1", "true", "True"}
        # Set browser path if provided
        browsers_path = os.getenv("PLAYWRIGHT_BROWSERS_PATH")
        launch_args = {"headless": headless}
        if browsers_path:
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
        browser = pl.start().chromium.launch(**launch_args)
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        self._page = ctx.new_page()
        return self._page

    def open(self, url: str) -> None:
        page = self._ensure_page()
        page.goto(url)

    def is_logged_in(self) -> bool:
        """Check if user is logged into YC by looking for profile elements."""
        page = self._ensure_page()
        # Check for elements that only appear when logged in
        # Either "View profile" buttons or profile cards
        return (
            page.locator('button:has-text("View profile")').count() > 0 or
            page.locator('.profile-card').count() > 0 or
            page.locator('[data-test="profile"]').count() > 0
        )

    # Convenience internal helper
    def _click_by_labels(self, labels: Iterable[str]) -> bool:
        page = self._ensure_page()
        for label in labels:
            try:
                btn = page.get_by_role("button", name=label)
                if btn.count() > 0:
                    btn.first.click()
                    return True
            except Exception:
                pass
            try:
                link = page.get_by_role("link", name=label)
                if link.count() > 0:
                    link.first.click()
                    return True
            except Exception:
                pass
            try:
                el = page.get_by_text(label, exact=True)
                if el.count() > 0:
                    el.first.click()
                    return True
            except Exception:
                pass
            try:
                el2 = page.get_by_text(label)  # non-exact
                if el2.count() > 0:
                    el2.first.click()
                    return True
            except Exception:
                pass
        return False

    def click_view_profile(self) -> bool:
        return self._click_by_labels(["View profile", "Open profile", "Profile"])

    def read_profile_text(self) -> str:
        page = self._ensure_page()
        try:
            # Prefer main content region if available
            main = page.get_by_role("main")
            if main.count() > 0:
                txt: str = main.inner_text()
                return txt
        except Exception:
            pass
        body_txt: str = page.inner_text("body")
        return body_txt

    def focus_message_box(self) -> None:
        page = self._ensure_page()
        try:
            el = page.get_by_role("textbox")
            el.first.click()
            return
        except Exception:
            pass
        # fallback textarea
        page.locator("textarea").first.click()

    def fill_message(self, text: str) -> None:
        page = self._ensure_page()
        try:
            el = page.get_by_role("textbox")
            el.first.fill(text)
            return
        except Exception:
            pass
        page.locator("textarea").first.fill(text)

    def send(self) -> None:
        if self._click_by_labels(["Send", "Submit", "Post"]):
            return
        # fallback: press Enter in focused textbox
        page = self._ensure_page()
        page.keyboard.press("Enter")

    def skip(self) -> None:
        self._click_by_labels(["Skip"])  # best-effort

    def verify_sent(self) -> bool:
        page = self._ensure_page()
        try:
            tb = page.get_by_role("textbox")
            if tb.count() > 0:
                val: str = tb.first.input_value()
                return val.strip() == ""
        except Exception:
            pass
        try:
            toast = page.get_by_text("Message sent")
            ok: bool = toast.count() > 0
            return ok
        except Exception:
            return False

    def close(self) -> None:
        try:
            if self._page is not None:
                ctx = self._page.context
                ctx.close()
        finally:
            if self._pl is not None:
                try:
                    self._pl.stop()
                except Exception:
                    pass
            self._pl = None
            self._page = None

    def __enter__(self) -> PlaywrightBrowser:  # pragma: no cover
        return self

    def __exit__(self, *_: object) -> None:  # pragma: no cover
        self.close()
