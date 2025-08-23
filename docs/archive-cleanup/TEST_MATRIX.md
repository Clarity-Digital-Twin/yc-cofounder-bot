# Test Matrix and Coverage Gaps

## Feature → Tests mapping
- CUA Responses API loop
  - tests/unit/test_openai_cua_browser.py: end-to-end loop, actions, safety checks, screenshot encoding, stop flag, previous_response_id chaining
- Playwright BrowserPort (sync)
  - tests/integration/test_browser_port.py: method existence and local HTML smoke
- AutonomousFlow orchestration
  - tests/integration/test_autonomous_flow.py: limit, stop flag, duplicates, send on YES, shadow mode, ordering, error handling, auto-send behavior
- Use cases
  - tests/unit/test_use_cases.py: evaluate+render combo; send respects quota and calls browser
  - tests/unit/test_send_verify.py: retry once then success or fail
- UI (Streamlit)
  - tests/unit/test_ui_streamlit.py: setup, session state, columns, selector options, STOP control, HIL panel, screenshot panel, start button validation, mode selection
- Decision adapter and schema
  - tests/unit/test_openai_decision_adapter.py: adapter returns schema-like payload and logs usage
  - tests/unit/test_schema.py: DTO literals and validation
- Rendering and scoring
  - tests/unit/test_templates_renderer.py: slots, bans, clamp
  - tests/unit/test_scoring.py: keyword and weighted scoring
- Quota and persistence
  - tests/unit/test_sqlite_quota.py, test_sqlite_progress.py, test_stop_flag.py: repos and stop flag
  - tests/integration/test_sqlite_repo.py: seen repo roundtrip

## Gaps to add
- Async singleton Playwright path + auto-login
  - Add unit/integration test for `PlaywrightBrowserAsync` with `AsyncLoopRunner`.
- Model resolver smoke test
  - Simulate `client.models.list()` with mock data: ensure proper fallback selection and env set.
- STOP re-check before send
  - Add unit test to assert `SendMessage` respects stop callback.
- CUA non-blocking OpenAI calls
  - Unit test that `_cua_action` awaits `asyncio.to_thread(...)` (can patch and assert threading or awaitable call).
- File quota vs SQLite default
  - Test DI path default selection and behavior under env flags.

