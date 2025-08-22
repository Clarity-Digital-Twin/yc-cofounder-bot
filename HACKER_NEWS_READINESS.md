# Hacker News Launch Readiness

## Demo Video Script
- Open Streamlit at `/` with 3-input UI enabled (`USE_THREE_INPUT_UI=true`).
- Paste a concise “Your Profile”, “Match Criteria”, and keep default message template.
- Choose mode: Hybrid (default) with threshold ~0.7.
- Ensure `ENABLE_CUA=0`, `ENABLE_PLAYWRIGHT=1` (Playwright-only path for speed and reliability).
- Click “Start Autonomous Browsing”.
- Show logs: decisions emitted, dedupe working, STOP flag indicator.
- Show a successful “Sent” with verification (shadow off) or shadow-mode dry run.

## Known Limitations to Disclose
- CUA is experimental and off by default; recommended Playwright-only for YC site.
- Model auto-resolution optional; provide a working `OPENAI_DECISION_MODEL` in `.env`.
- Headless reliability depends on local Playwright install; demo uses headed mode.

## Minimum Fixes Required
- P0 items from `REFACTOR_PRIORITY_LIST.md`:
  - Make CUA OpenAI calls non-blocking (executor) and clear cache on nav/skip.
  - Add STOP re-check in send path and avoid blocking sleeps from UI.
  - Optionally wire model resolver at startup or lock to a documented model.
  - Consider DI toggle for `PlaywrightBrowserAsync` (singleton + auto-login) or clarify docs that default is manual login.

## Suggested Tagline
- “Open-source YC cofounder matcher: deterministic Playwright navigation + pluggable AI decisions, with optional Computer Use planning.”

