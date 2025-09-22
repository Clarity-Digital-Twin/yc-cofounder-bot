# Full Code Audit (Module-by-Module)

Scope: Deep audit of src/ and tests/, mapping responsibilities, correctness, risks, and actions required for a polished MVP launch.

## Package Overview
- application: Ports, use cases, orchestrator (AutonomousFlow)
- domain: Entities and scoring services (pure)
- infrastructure: Adapters (OpenAI, Playwright, SQLite, logging), helpers
- interface: Web UI (Streamlit), CLI, DI wiring
- tests: Unit and integration coverage across flows

## application/
- ports.py: Contracts for DecisionPort, MessagePort, ScoringPort, QuotaPort, BrowserPort, ProgressRepo, StopController, LoggerPort.
  - Status: Clear and consistent. BrowserPort is synchronous by design.
  - Risk: Several tests assume async methods on browser; solve via adapters or adjust tests.

- use_cases.py: EvaluateProfile (combines decision + render) and SendMessage (quota check, send, verify with retry), ProcessCandidate (single-URL gated flow).
  - Status: Correct and cohesive. SendMessage includes pacing and retry once.
  - Risks:
    - Blocking `time.sleep` impacts UI responsiveness.
    - No STOP re-check before send.
  - Actions: Make pacing optional/non-blocking; add STOP re-check before send.

- autonomous_flow.py: Main orchestrator for autonomous browsing; dedupe, decision, optional send, logging, and error continuation.
  - Status: Solid structure; checks STOP at head; logs thoroughly.
  - Risks: No bounded retries, STOP not re-checked within send path; relies on sync BrowserPort (ok for DI default).
  - Actions: Add small backoff retry on read/skip; call STOP before send.

- schema.py: Pydantic DTOs (validated in tests).
  - Status: OK.

## domain/
- entities.py: Criteria, Profile, Score, Decision dataclasses.
- services.py: ScoringService (keyword count) and WeightedScoringService (token weights).
  - Status: Pure, test-covered and deterministic.

## infrastructure/
- openai_decision.py: `OpenAIDecisionAdapter` uses `client.responses.create` and logs usage with token-derived cost estimates.
  - Status: Works; agnostic to SDK; stamped usage emitted.
  - Docs mismatch: Some docs claim Chat Completions; code uses Responses API which is fine. Update docs.
  - DTO naming mismatch: Adapter stamps `prompt_ver`/`rubric_ver`, while `DecisionDTO` defines `prompt_version`. Align names or map when serializing.

- openai_cua_browser.py: Responses API loop (`computer_use_preview`) + Playwright execution. Sync BrowserPort facade calls internal async via `asyncio.run`. Safety checks, STOP, screenshot callback, HIL callback supported.
  - Status: Architecturally correct. Tests verify the loop, safety checks, chaining, and screenshot encoding.
  - Risks:
    - `responses.create` is blocking inside async functions → event loop starvation with real network.
    - `asyncio.run` fails if called inside an active loop (e.g., Streamlit async contexts).
    - `_profile_text_cache` reuse might return stale text across pages.
    - HIL callback assumed async.
  - Actions:
    - Wrap OpenAI calls with `await asyncio.to_thread(self.client.responses.create, ...)` inside async methods.
    - Replace `asyncio.run` facade with a runner pattern when loop is running (or provide Async adapter for tests/UI).
    - Clear cache on `open()` and `skip()`.
    - Accept sync/async HIL callbacks.

- browser_playwright.py: Sync Playwright adapter implementing BrowserPort; deterministic selectors and simple heuristics.
  - Status: Works; integration tests cover it.

- browser_playwright_async.py + async_loop_runner.py: Async singleton browser with background event loop thread; optional auto-login for YC.
  - Status: Robust design; not selected by DI. Good fallback for environments with event loop constraints.
  - Action: Add DI flag to select this adapter (`ENABLE_PLAYWRIGHT_ASYNC=1`).

- sqlite_repo.py, sqlite_progress.py, sqlite_quota.py: Simple SQLite repos for dedupe, progress, and quotas. Daily/weekly quota is atomic in DB. File quota is non-atomic.
  - Actions: Prefer SQLiteDailyWeeklyQuota by default for safety.

- jsonl_logger.py, logger_stamped.py: Event logging with stamps; used broadly.
  - Status: Good.

- local_decision.py: Simple YES decision placeholder with extracted name. Used as fallback.
  - Status: Fine for offline/dev.

- template_loader.py, templates.py: Template load with banned phrases and clamping.
  - Status: Good; test covered.

- click_helpers.py, normalize.py: Retry helpers, normalization and hashing.
  - Status: Good.

- model_resolver.py: Finds GPT-5/5-thinking then falls back to GPT-4; can resolve CUA models; emits results.
  - Status: Solid; not wired in DI.

## interface/
- di.py: Wires decision adapters, logger, quota, and browser. CUA primary via env, else Playwright, else noop.
  - Status: Working; logger stamped, hybrid gating supported.
  - Risks: Doesn’t use `model_resolver.py`; CUA selection assumes sync BrowserPort (fine), no async singleton option.
  - Actions: Optionally call resolver once and set env; add `ENABLE_PLAYWRIGHT_ASYNC` branch to use async singleton.

- web/ui_streamlit.py: Three-input autonomous UI and paste-mode UI with STOP/HIL/screenshot support. Builds services via DI and runs AutonomousFlow.
  - Status: Functional. Tests cover UI wiring and behavior.
  - Risks: If underlying BrowserPort uses `asyncio.run` in a loop context, collisions may occur; default Playwright sync avoids this.

- cli/check_cua.py: Checks Agents SDK availability; not aligned with Responses API approach.
  - Action: Keep as diagnostic; note in docs it’s optional/legacy for capability probing only.

- cli/run.py: Paste-mode CLI (partially truncated in view); no issues expected.

## tests/
- Broad coverage of CUA loop (unit), Playwright adapter (integration), AutonomousFlow orchestration (integration), UI components (unit), rendering, schema, scoring, quotas, stop flag, etc.
- Gaps:
  - No tests for async singleton adapter path / auto-login.
  - No tests for model resolver integration.
  - No tests for STOP re-check in send path.
  - No tests for non-blocking CUA OpenAI calls.

## Cross-Doc Contradictions (Actionable)
- GPT-5-only claims vs fallback reality → Update docs to allow resolver fallback to GPT‑4 family when 5 is unavailable.
- "CUA primary" vs recommended Playwright default → Clarify positioning.
- Auto-login & singleton claimed as default → Either wire via DI flag or tone down claim.

## MVP Action Plan (No Yak-Shaving)
1) CUA async safety: thread off `responses.create` calls; clear cache on nav/skip; accept sync/async HIL.
2) Send path STOP gate + non-blocking pacing under UI.
3) Prefer SQLite quota in DI by default (or clear doc for enabling it).
4) Optional: DI flag for async singleton Playwright; otherwise document manual login.
5) Wire (or document) model resolver usage at startup.
6) Tests: add focused unit tests for 1–2 above and a smoke test for resolver.
