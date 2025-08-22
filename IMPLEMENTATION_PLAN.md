# Implementation Plan (Concrete, Self-Contained)

Purpose: A step-by-step, execution-ready plan to polish the repo to a reliable MVP that any contributor (human or AI) can follow without prior context.

Read this file top-to-bottom and implement in order. Each task lists files, exact changes, acceptance tests, and verification commands.

## Conventions
- Paths are relative to repo root. Python sources under `src/`.
- Run commands with: `make setup && make browsers` once, then `make verify` as needed.
- Env flags used in plan:
  - `PACE_BLOCKING` (0 = non-blocking in UI, 1 = blocking sleeps)
  - `ENABLE_PLAYWRIGHT_ASYNC` (use async singleton adapter)
  - `ENABLE_MODEL_RESOLUTION` (auto-resolve models at startup)

## P0: Blockers (Must Implement First)

1) CUA async safety: run OpenAI calls off the event loop
- Files: `src/yc_matcher/infrastructure/openai_cua_browser.py`
- Goal: Ensure all OpenAI client calls inside async functions do not block the event loop.
- Changes:
  - Add a helper method inside the class:
    - `async def _responses_create_async(self, **kwargs) -> Any: return await asyncio.to_thread(self.client.responses.create, **kwargs)`
  - Replace every `self.client.responses.create(...)` inside async methods (e.g., `_cua_action`) with `await self._responses_create_async(...)`.
- Acceptance:
  - `pytest -q tests/unit/test_cua_async_safety.py::TestCUAAsyncSafety::test_openai_calls_dont_block_event_loop` passes.
  - No regressions in other CUA unit tests.

2) CUA cache hygiene on navigation/skip
- Files: `src/yc_matcher/infrastructure/openai_cua_browser.py`
- Goal: Avoid stale profile text reuse.
- Changes:
  - At the start of `_open_async(self, url: str)`, set `self._profile_text_cache = ""` before navigation logic.
  - At the end of `_skip_async(self)`, set `self._profile_text_cache = ""` after performing the skip action.
- Acceptance:
  - `pytest -q tests/unit/test_cua_async_safety.py::TestProfileCacheClearing` tests pass.

3) Async/sync boundary guard in CUA sync facade
- Files: `src/yc_matcher/infrastructure/openai_cua_browser.py`
- Goal: Prevent `asyncio.run(...)` from being called when an event loop is already running (e.g., Streamlit).
- Changes:
  - For each sync wrapper (`open`, `click_view_profile`, `read_profile_text`, `focus_message_box`, `fill_message`, `send`, `verify_sent`, `skip`, `close`):
    - Implement a small helper `_run(self, coro: Awaitable[T]) -> T`:
      - If `asyncio.get_event_loop().is_running()` (or `asyncio.get_running_loop()`), schedule via `asyncio.run_coroutine_threadsafe` to a lazily created background loop (similar to `AsyncLoopRunner` pattern) OR, simplest: document that UI uses Playwright sync adapter; guard only for tests to avoid double loops.
    - For this MVP, choose the simpler guard: if loop running, raise a clear error asking to use Playwright sync adapter in UI. Otherwise, call `asyncio.run(coro)`.
- Acceptance:
  - Streamlit path continues to use Playwright sync (default), no loop errors.
  - Unit tests that call async internals directly still pass.

4) SendMessage: STOP gates and non-blocking pacing
- Files: `src/yc_matcher/application/use_cases.py`
- Goal: Honor STOP during the send pipeline and avoid blocking UI threads with sleep.
- Changes:
  - Modify `@dataclass SendMessage` to accept `stop: StopController | None = None`.
  - Emit `logger.emit({"event": "stopped", "where": "send_message_start"})` and return False if stopped at start.
  - Before focus: check STOP, emit `{where: "before_focus"}`.
  - After focus (before fill): check STOP, emit `{where: "after_focus"}`.
  - Before send: check STOP, emit `{where: "before_send"}`.
  - Before retry send: check STOP, emit `{where: "before_retry"}`.
  - Pacing: read `PACE_BLOCKING` env. If `0`, skip `time.sleep`; if `1` (default), keep sleeping behavior.
- Acceptance:
  - Update/add tests in `tests/unit/test_event_schemas.py` to assert events and STOP gating.
  - `tests/unit/test_send_verify.py` still pass for both retry paths.

5) DTO naming consistency (adapter vs schema)
- Files: `src/yc_matcher/infrastructure/openai_decision.py`, `src/yc_matcher/application/schema.py`
- Goal: Ensure consistent key names for prompt versions.
- Changes (either approach is fine; choose one):
  - A) Change adapter to emit `prompt_version` instead of `prompt_ver` and keep `rubric_ver` separate; OR
  - B) Keep adapter as-is and document mapping when serializing to DTOs.
- Acceptance:
  - No consumer breaks; schema validation tests remain green.

## P1: Important (Should Implement Next)

6) DI safer defaults and async adapter toggle
- Files: `src/yc_matcher/interface/di.py`
- Goal: Improve reliability with better defaults and optional async adapter.
- Changes:
  - Default quota to `SQLiteDailyWeeklyQuota` unless `FILE_QUOTA=1`.
  - Add `ENABLE_PLAYWRIGHT_ASYNC=1` branch that imports and uses `PlaywrightBrowserAsync` instead of the sync Playwright when CUA is disabled.
  - Keep `_NullBrowser` only when neither CUA nor any Playwright flag is set.
- Acceptance:
  - Extend `tests/unit/test_di.py` to verify selection logic under env toggles.

7) Optional: model resolution wiring
- Files: `src/yc_matcher/infrastructure/model_resolver.py`, `src/yc_matcher/interface/di.py`
- Goal: Resolve models at startup when enabled, else use env.
- Changes:
  - Add `ENABLE_MODEL_RESOLUTION=1` flag; in DI (or UI/CLI entry), call `resolve_and_set_models(logger)` once; use `DECISION_MODEL_RESOLVED`/`CUA_MODEL_RESOLVED` if present.
- Acceptance:
  - New `tests/unit/test_model_resolver.py` mocking `client.models.list()` exercising: has gpt-5-thinking; has only gpt-5; has only gpt-4*.

8) AutonomousFlow bounded retries
- Files: `src/yc_matcher/application/autonomous_flow.py`
- Goal: Improve resilience on transient read/skip failures.
- Changes:
  - Wrap `read_profile_text()` and `skip()` in a small `for attempt in range(2)` loop with a short sleep/backoff; log retry.
  - Re-check STOP before retrying.
- Acceptance:
  - Existing integration tests pass; add a focused unit/integration test simulating transient exception followed by success.

## P2: Nice-to-Have (Quality)

9) HIL callback ergonomics
- Files: `src/yc_matcher/infrastructure/openai_cua_browser.py`
- Goal: Support both sync and async callbacks.
- Changes:
  - In `_hil_acknowledge`, detect if callback returns a coroutine; if so `await` it, else wrap with `asyncio.to_thread` or call directly in executor.
- Acceptance:
  - Add a unit test passing both sync and async callbacks.

10) CLI diagnostics clarification
- Files: `src/yc_matcher/interface/cli/check_cua.py`
- Goal: Set expectations for Agents SDK-based check vs Responses API.
- Changes:
  - Update docstring with “diagnostic (Agents SDK)”, print hint about Responses API loop as the production integration.
- Acceptance:
  - No behavioral change required; doc clarity only.

## Documentation Updates

11) Align positioning and claims
- Files: `README.md`, `SSOT.md`, `CANONICAL_TRUTH.md`
- Edits:
  - Decisions use OpenAI Responses API; GPT‑5/-thinking preferred, but resolver may select GPT‑4 family; Playwright-only is the default for YC; CUA is experimental/opt-in.
  - Mention `ENABLE_PLAYWRIGHT_ASYNC` for singleton + optional auto-login path.

12) Operations Runbook
- Files: `docs/OPERATIONS.md` (new)
- Content:
  - Env templates, `make browsers`, headed (`PLAYWRIGHT_HEADLESS=0`) vs headless (`=1`) operation, quotas (SQLite default), STOP flag usage, enabling CUA and async Playwright, troubleshooting common errors.

## Tests: Add/Adjust (Summary)
- Add/extend:
  - `tests/unit/test_event_schemas.py` (STOP gates + where contexts; PACE_BLOCKING behavior)
  - `tests/unit/test_model_resolver.py` (mocked model list)
  - Optional: `tests/integration/test_single_browser.py` to exercise `ENABLE_PLAYWRIGHT_ASYNC=1`
- Ensure existing tests remain green, especially:
  - `tests/unit/test_openai_cua_browser.py` (Responses API loop correctness)
  - `tests/integration/test_autonomous_flow.py` (flow orchestration)
  - `tests/integration/test_browser_port.py` (Playwright sync adapter)

## Verification & Release

13) Verification sequence
- Commands:
  - `make setup`
  - `make browsers`
  - `PACE_BLOCKING=0 make test` (UI-friendly pacing default)
  - `PLAYWRIGHT_HEADLESS=1 make test-int`
  - `make verify`

14) Demo readiness (per HACKER_NEWS_READINESS.md)
- Ensure Playwright-only path is default: `ENABLE_CUA=0`, `ENABLE_PLAYWRIGHT=1`.
- 3-input UI, Hybrid mode, shadow off for demo; confirm send + verify events and dedupe.

## Definition of Done
- All P0 and P1 items implemented and tests updated.
- `make verify` green locally (headed) and headless integration tests pass.
- README/SSOT/CANONICAL_TRUTH updated to match reality.
- Short demo recorded per HACKER_NEWS_READINESS.md.

