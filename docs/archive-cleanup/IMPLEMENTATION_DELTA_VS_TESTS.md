# Implementation vs Tests: Deltas to Close

This file lists discrepancies between current implementation and expectations encoded in tests. Closing these gaps will make the suite consistent and reduce regressions.

## SendMessage event schemas and STOP gates
- Tests: tests/unit/test_event_schemas.py
  - Expectation:
    - `SendMessage` accepts a `stop` controller (can be None).
    - Emits `stopped` events with a `where` key at specific checkpoints (start, before_focus, after_focus, before_send, before_retry).
    - Emits `quota_block` with `limit` always present.
  - Current implementation:
    - `SendMessage` signature has no `stop`.
    - Emits `quota_block` with `limit` (OK), but does not emit `stopped` in send path.
  - Action:
    - Add optional `stop: StopController | None` to `SendMessage`.
    - Emit `stopped` event with `where` context at the checkpoints above.

## CUA async safety and cache clearing
- Tests: tests/unit/test_cua_async_safety.py
  - Expectation:
    - OpenAI `responses.create` does not block the event loop (run in executor/thread).
    - `_profile_text_cache` is cleared on navigation and skip.
  - Current implementation:
    - Uses blocking client calls in async methods; cache is not explicitly cleared on navigation/skip.
  - Action:
    - Wrap client calls with `await asyncio.to_thread(...)`.
    - Set `self._profile_text_cache = ""` in `_open_async` and `_skip_async`.

## Browser singleton behavior
- Tests: tests/integration/test_single_browser.py
  - Expectation:
    - Async singleton runner ensures no repeated launches.
  - Current implementation:
    - Async runner exists, but DI does not surface this adapter; test patches runner/playwright and imports `OpenAICUABrowser`, which is OK.
  - Action:
    - No change required for the test; keep runner import path stable.

## BrowserPort sync contract
- Tests: tests/unit/test_browser_port_sync.py
  - Expectation: All BrowserPort methods are synchronous.
  - Current implementation: Matches expectation.

## DI tests
- Tests: tests/unit/test_di.py, tests/unit/test_decision_modes.py
  - Expectation: DI constructs correct adapters per mode; logger stamping; hybrid gate behavior.
  - Current implementation: Should pass; minor risk if env defaults differ.

## Minor
- Model resolver tests (missing): Add if we wire resolver.
- STOP-in-send test (missing): Add once `SendMessage` gains stop gates.

