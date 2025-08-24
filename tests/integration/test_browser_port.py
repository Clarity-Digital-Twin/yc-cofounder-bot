import pytest

pytest.importorskip("playwright.sync_api", reason="Playwright not installed")


@pytest.mark.integration
def test_adapter_exposes_expected_methods():
    from yc_matcher.infrastructure.browser.playwright_sync import PlaywrightBrowser

    b = PlaywrightBrowser()
    for name in (
        "open",
        "click_view_profile",
        "read_profile_text",
        "focus_message_box",
        "fill_message",
        "send",
        "skip",
        "verify_sent",
        "close",
    ):
        assert hasattr(b, name)


HTML = """
<!doctype html><meta charset="utf-8">
<main>
  <a role="link" href="#" id="view">View profile</a>
  <section id="profile">Hi, I am a test profile</section>
  <textarea id="msg"></textarea>
  <button id="send">Send</button>
  <div id="toast" style="display:none;">Message sent</div>
  <script>
  document.getElementById('send').addEventListener('click', () => {
    const tb = document.getElementById('msg');
    tb.value = '';
    document.getElementById('toast').style.display = 'block';
  });
  </script>
  </main>
"""


@pytest.mark.integration
def test_smoke_local_html(tmp_path, monkeypatch):
    from yc_matcher.infrastructure.browser.playwright_sync import PlaywrightBrowser

    monkeypatch.setenv("PLAYWRIGHT_HEADLESS", "1")
    html_path = tmp_path / "page.html"
    html_path.write_text(HTML, encoding="utf-8")

    b = PlaywrightBrowser()
    try:
        b.open(f"file://{html_path}")
        assert b.click_view_profile() is True
        assert "test profile" in b.read_profile_text()
        b.focus_message_box()
        b.fill_message("Hello world")
        b.send()
        assert b.verify_sent() is True
    finally:
        b.close()
