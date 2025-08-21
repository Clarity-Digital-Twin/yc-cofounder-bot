# Codebase Audit and Flow Validation

Scope: Validate data flows, code paths, and tests against Mermaid diagrams; highlight mismatches and propose changes to reach a reliable, flaw-free bot.

## Verified Flows
- UI wiring: `ui_streamlit.py` builds services via `build_services()` and runs `AutonomousFlow.run(...)`. HIL and screenshot callbacks are passed to CUA when enabled.
- DI decisions: `di.create_decision_adapter()` selects advisor/rubric/hybrid per env or parameter. OpenAI decision uses `client.responses.create` and stamps usage via `LoggerWithStamps`.
- Browser selection: CUA primary (`ENABLE_CUA=1`), Playwright fallback (`ENABLE_PLAYWRIGHT[_FALLBACK]=1`), or `_NullBrowser`.
- Autonomous loop: `AutonomousFlow.run()` processes up to `limit`, checks STOP at loop head, handles duplicates via `SQLiteSeenRepo`, logs decisions, auto-sends via `SendMessage` when allowed.
- Quota: file-based (`FileQuota`) or calendar-aware (`SQLiteDailyWeeklyQuota`) per env flag.
- Events: JSONL logger at `.runs/events.jsonl` with stamped versions.

## Mermaid Corrections (applied in ARCHITECTURE_MERMAID.md)
- Browser path: current code sets `PLAYWRIGHT_BROWSERS_PATH` before `async_playwright().start()`; updated doc to reflect this and reframe failures as potential, not current.
- Responses API: CUA uses `client.responses.create()` with `computer_use_preview` tool; removed the outdated “not using Responses API” bug.
- Failure modes: clarified async/sync boundary issues and loop-blocking risks.

## Key Mismatches and Risks
- Async/sync mismatch:
  - Ports and `AutonomousFlow` expect sync browser methods, implemented via `asyncio.run(...)` wrappers.
  - Several tests call `await browser.open()` / `await browser.read_profile_text()`, which will fail against the current sync signatures.
  - Recommendation: keep the sync `BrowserPort` in app; add an async adapter (thin wrappers around `_xxx_async`) for tests, or teach tests to call sync methods.

- CUA blocking calls in async methods:
  - `responses.create(...)` is synchronous inside `_cua_action` loop; under real network, this will block the event loop.
  - Recommendation: wrap in `await asyncio.to_thread(self.client.responses.create, ...)`.

- STOP check coverage:
  - STOP gate exists at loop head and inside CUA loop, but `SendMessage` does not re-check before send.
  - Recommendation: re-check STOP just before sending, and shorten pacing when STOP is set.

- Pacing blocks UI thread:
  - `time.sleep(PACE_MIN_SECONDS)` blocks Streamlit thread when sends occur via UI.
  - Recommendation: make pacing optional in UI context or move waits out of the UI thread.

- Quota atomicity (file):
  - `FileQuota` is not atomic across processes; SQLite quota is already available and preferred when `ENABLE_CALENDAR_QUOTA=1`.
  - Recommendation: default to SQLite quota for all modes or add a file lock.

- Profile cache semantics:
  - `_profile_text_cache` retains last non-empty text; can mask true empty result after navigation.
  - Recommendation: clear the cache on navigation/skip.

- HIL callback robustness:
  - Expects an async callback; handle sync callables gracefully.

## Recommended Changes (Minimal, High-Impact)
1) Add async-safe OpenAI call in CUA:
   - Use `asyncio.to_thread(self.client.responses.create, ...)` anywhere it’s called inside async methods.

2) Introduce Async Test Adapter or dual-interface methods:
   - Option A: Create `OpenAICUABrowserAsyncTest` where methods are `async def` and call the existing internals.
   - Option B: Detect running loop and route: if loop running, call `_xxx_async` directly; else `asyncio.run(...)`. Update tests accordingly.

3) Re-check STOP before send:
   - In `SendMessage.__call__`, check a `StopController` or pass a callable to bail pre-send.

4) Non-blocking pacing:
   - Make pacing optional (env or param). In Streamlit, skip `time.sleep` and rely on a lightweight wait or a queue.

5) Prefer SQLite quota by default:
   - Flip default or document enabling `ENABLE_CALENDAR_QUOTA=1` for multi-run safety.

6) Clear profile cache at navigation/skip:
   - Set `_profile_text_cache = ""` when opening a new URL or after `skip()`.

## Next Steps (if you want me to implement)
- Patch CUA to use `asyncio.to_thread` for OpenAI calls, and clear the profile cache on navigation/skip.
- Add STOP re-check and optional non-blocking pacing in `SendMessage` (behind env flag).
- Add a small async adapter for tests or update tests to call sync methods for `BrowserPort`.
- Tighten docs in README with environment and Playwright install notes.

