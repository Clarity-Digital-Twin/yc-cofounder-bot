# Completion Checklist (Exhaustive, Code-Driven)

This consolidates all fixes and decisions required to deliver a tight MVP suitable for HN.

## Architecture & Flow
- Align docs to reality: Decisions via Responses API; Playwright-only is default; CUA is experimental and opt-in.
- Update diagrams for async/sync edges (done in ARCHITECTURE_MERMAID.md).

## OpenAI CUA (src/yc_matcher/infrastructure/openai_cua_browser.py)
- Run blocking calls off the event loop:
  - Wrap `client.responses.create(...)` with `await asyncio.to_thread(...)` in async paths.
- Async/sync boundary:
  - Avoid `asyncio.run()` when a loop is running (UI/tests). Option A: add an Async adapter; Option B: detect running loop and delegate.
- Cache hygiene:
  - Clear `_profile_text_cache` in `_open_async` and `_skip_async`.
- HIL callback ergonomics:
  - Accept sync and async callbacks in `_hil_acknowledge`.

## Decisions & Schema
- OpenAIDecisionAdapter (src/yc_matcher/infrastructure/openai_decision.py):
  - Keep Responses API; ensure consistent keys with DTOs.
- DTO naming:
  - Align `prompt_ver`/`rubric_ver` with `DecisionDTO` fields (or add mapping layer).
- Model resolution (src/yc_matcher/infrastructure/model_resolver.py):
  - Optional: call at startup; set `DECISION_MODEL_RESOLVED`/`CUA_MODEL_RESOLVED` and consume in DI.
  - Update docs to allow GPT‑4 fallback when GPT‑5 not available.

## Browser Adapters
- Playwright (sync) (src/yc_matcher/infrastructure/browser_playwright.py):
  - No changes required; proven via integration tests.
- Async singleton + auto-login (src/yc_matcher/infrastructure/browser_playwright_async.py):
  - Add DI flag `ENABLE_PLAYWRIGHT_ASYNC=1` to opt-in; document behavior.

## Use Cases & Orchestrator
- SendMessage (src/yc_matcher/application/use_cases.py):
  - Add optional `stop: StopController | None`.
  - Emit `stopped` events with `where` at “send_message_start”, “before_focus”, “after_focus”, “before_send”, “before_retry”.
  - Re-check stop before sending and before retry.
  - Make pacing non-blocking in UI context; add `PACE_BLOCKING=0` to disable `time.sleep`.
- AutonomousFlow (src/yc_matcher/application/autonomous_flow.py):
  - Add small bounded retries around `read_profile_text()`/`skip()`.
  - Optionally check STOP again before `send`.

## Quotas & Persistence
- Prefer SQLite quota by default in DI for atomicity across processes.
- File quota path: document non-atomicity or add a simple file lock.

## UI (src/yc_matcher/interface/web/ui_streamlit.py)
- Non-blocking runs:
  - Ensure browser adapter used in UI won’t call `asyncio.run` inside Streamlit’s loop (prefer sync Playwright or async runner adapter).
- HIL & screenshots:
  - Keep current; after HIL/STOP fixes above, UI will reflect state.

## CLI & Diagnostics
- CLI run: ok.
- `check_cua.py`: mark as diagnostic (Agents SDK); optional to add a Responses API checker.

## Tests: Add/Adjust
- Add tests for:
  - STOP re-check path and event schema in SendMessage.
  - Async singleton Playwright adapter smoke.
  - Model resolver smoke (mocked models). 
  - CUA non-blocking calls (already partially there) and cache clearing (already present).
- Adjust tests expecting async BrowserPort if we retain sync-only port; or expose an async test adapter.

## Ops & Docs
- README/SSOT/CANONICAL_TRUTH:
  - Update model claims (allow fallback), CUA positioning, and Playwright defaults.
- Add a short “Operations Runbook”: env examples, `make browsers`, headless guidance.

## Release
- Implement P0/P1 above, run `make verify` in both headed and headless.
- Record demo per HACKER_NEWS_READINESS.md.
- Ship.

