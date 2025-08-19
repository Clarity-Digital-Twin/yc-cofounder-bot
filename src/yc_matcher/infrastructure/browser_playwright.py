from __future__ import annotations

from collections.abc import Iterable

try:
    from playwright.sync_api import Page, sync_playwright  # type: ignore
except Exception:  # pragma: no cover
    Page = object  # type: ignore
    sync_playwright = None  # type: ignore


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
            raise RuntimeError("Playwright not available; install with `python -m playwright install chromium`")
        self._pl = sync_playwright().start()
        browser = self._pl.chromium.launch(headless=False)
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        self._page = ctx.new_page()
        return self._page

    def open(self, url: str) -> None:
        page = self._ensure_page()
        page.goto(url)

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
                el = page.get_by_text(label, exact=True)
                if el.count() > 0:
                    el.first.click()
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
                return main.inner_text()
        except Exception:
            pass
        return page.inner_text("body")

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

