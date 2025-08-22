# Refactoring Priority List

## P0 - Blockers (before HN launch)
1. Async/sync boundary safety in CUA calls – run OpenAI `responses.create` in a thread from async context
   - File: `src/yc_matcher/infrastructure/openai_cua_browser.py` (calls in `_cua_action`)
   - Effort: S (1–2 hrs)

2. Re-check STOP before sending and avoid blocking sleep in UI path
   - File: `src/yc_matcher/application/use_cases.py` (`SendMessage.__call__`)
   - Effort: S (1 hr)

3. Wire model resolution (optional but recommended) or clearly document fixed model usage
   - Files: `src/yc_matcher/interface/di.py` (call resolver at startup), `infrastructure/model_resolver.py`
   - Effort: M (2–4 hrs)

4. Align DI with singleton Playwright + optional auto-login OR explicitly document current default
   - Files: `src/yc_matcher/interface/di.py` (optionally use `PlaywrightBrowserAsync` when enabled)
   - Effort: M (2–4 hrs)

## P1 - Critical (should fix)
1. Clear profile text cache on navigation/skip to avoid stale reuse
   - File: `openai_cua_browser.py` (`open`, `skip`)
   - Effort: S

2. Make `BrowserPort` test ergonomics consistent (provide async test adapter or adjust tests)
   - Files: tests expecting `await browser.*`, port is sync – add async adapter or wrappers
   - Effort: M

3. Improve error recovery in `AutonomousFlow` (bounded retries on transient read/skip failures)
   - File: `application/autonomous_flow.py`
   - Effort: M

4. Prefer SQLite quota by default for multi-run/process safety
   - Files: `interface/di.py` default selection
   - Effort: S

## P2 - Nice to Have
1. Headless/CI stability toggles and docs (playwright install, args)
   - Files: README, Makefile, `async_loop_runner.py`
   - Effort: S

2. Streamline HIL callback to accept sync or async functions
   - File: `openai_cua_browser.py`
   - Effort: S

3. Minor doc cleanup: unify model claims, clarify CUA positioning vs Playwright
   - Files: README, SSOT.md, CANONICAL_TRUTH.md
   - Effort: S

