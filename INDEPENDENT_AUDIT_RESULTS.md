# Independent Audit Results
Date: 2025-08-22
Auditor: Codex CLI (independent agent)

## Executive Summary
- Overall Status: ALMOST READY for Hacker News (with focused P0 fixes)
- Critical Issues: 4
- Major Issues: 4
- Minor Issues: 4

## Critical Findings

### 1. OpenAI CUA Implementation
Status: PARTIALLY WORKING
Evidence: `src/yc_matcher/infrastructure/openai_cua_browser.py` uses `client.responses.create(...)` with `computer_use_preview` and `previous_response_id` chaining; actions are executed via Playwright async API; safety checks and STOP flag are handled.
Reality: Correct Responses API pattern is implemented, but blocking sync calls are made from async context and there is an async/sync interface mismatch (see below). Fallback to raw Playwright exists and works.

### 2. Model Resolution
Status: PARTIAL (not wired)
Evidence: `src/yc_matcher/infrastructure/model_resolver.py` implements discovery, but DI (`src/yc_matcher/interface/di.py`) does not invoke it; `OpenAIDecisionAdapter` accepts a `model` env directly. Docs claim GPT-5/"thinking"; runtime may not have it.
Reality: Models are not auto-resolved at startup. The system should prefer a robust default (e.g., GPT-4 family) when GPT-5 is unavailable, while remaining honest in docs.

### 3. Browser Automation
Status: WORKING (Playwright fallback), PARTIAL (auto-login + singleton not wired by default)
Evidence: `PlaywrightBrowser` (sync) is DI default when CUA disabled. An advanced async singleton path exists (`AsyncLoopRunner` + `PlaywrightBrowserAsync`) with auto-login logic, but is not selected in DI.
Reality: Navigation, read, send, verify flows are implemented and used. Auto-login and singleton are available but not active by default.

### 4. Three-Input Flow (UI)
Status: WORKING
Evidence: `ui_streamlit.py` implements the 3-input autonomous UI behind `USE_THREE_INPUT_UI=true`. HIL approvals and screenshots are integrated when CUA is enabled. AutonomousFlow orchestrates evaluation and send.
Reality: Functional for MVP; STOP flag UI controls exist; shadow mode supported.

## What's Actually Working
- 3-input Streamlit UI with mode selection and safety controls.
- DI for advisor/rubric/hybrid; rubric-only path fully local and deterministic.
- AutonomousFlow orchestration including dedupe, decision logging, and send path.
- JSONL event logging and SQLite seen/quota repos.
- Playwright-only navigation & send adapter.
- CUA loop with Responses API and Playwright execution, including safety checks and STOP detection.

## What's Completely Broken
- None blocking basic MVP when using Playwright-only path (CUA disabled).

## What's Half-Implemented
- Model resolution: code exists but not plugged into DI/startup.
- Async browser singleton + auto-login: implemented but not selected by DI.
- CUA async/sync ergonomics: works with mocks; needs non-blocking OpenAI calls and clearer sync/async adapter split for tests.

## Major Contradictions Across Docs
- GPT-5/"thinking" claims vs code: Code supports any `OPENAI_DECISION_MODEL`; resolver can fall back to GPT-4, but docs forbid GPT-4. Update docs to reflect practical availability and resolver behavior.
- Auto-login and singleton: Present in async path, not default in DI. SSOT states singleton + auto-login as working defaults; adjust DI or docs.
- "CUA primary" vs "Playwright recommended": README emphasizes CUA+Playwright together; SSOT recommends Playwright-only as production default. Clarify positioning.

## Recommended Decision
- Ship MVP using Playwright-only (fast, deterministic), Hybrid/Rubric modes, shadow off. Keep CUA as opt-in experimental.

## Evidence Map (selected)
- CUA loop: `openai_cua_browser.py` methods `_cua_action`, `_execute_action`, `verify_sent`.
- DI wiring: `interface/di.py` selects CUA or Playwright; decision adapters and logger stamping.
- Async singleton: `infrastructure/async_loop_runner.py`, `infrastructure/browser_playwright_async.py` (not used by DI).
- Model resolver: `infrastructure/model_resolver.py` (not used by DI).

