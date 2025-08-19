import pytest

pytest.importorskip("playwright.sync_api", reason="Playwright not installed")


@pytest.mark.integration
def test_adapter_exposes_expected_methods():
    from yc_matcher.infrastructure.browser_playwright import PlaywrightBrowser

    b = PlaywrightBrowser()
    for name in (
        "open",
        "click_view_profile",
        "read_profile_text",
        "focus_message_box",
        "fill_message",
        "send",
        "skip",
    ):
        assert hasattr(b, name)

