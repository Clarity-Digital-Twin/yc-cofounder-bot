# True Architecture (What's Actually Built)

## Real Implementation Status

### OpenAI Integration
- Decision Model: Taken from `OPENAI_DECISION_MODEL` env or DI default; `OpenAIDecisionAdapter` uses `client.responses.create(...)` and logs usage when available.
- CUA Model: Taken from `CUA_MODEL` env; CUA loop implemented in `openai_cua_browser.py` using Responses API with `computer_use_preview` tool and `previous_response_id` chaining.
- Model Resolution: `infrastructure/model_resolver.py` can discover models but is not invoked by DI at startup.

### Browser Control
- Default DI: `OpenAICUABrowser` when `ENABLE_CUA=1`, else `PlaywrightBrowser` (sync) or `_NullBrowser`.
- Singleton/Auto-login Path: `AsyncLoopRunner` + `PlaywrightBrowserAsync` implement a single browser/page with optional auto-login, but DI does not select this by default.
- Verification: `verify_sent()` checks CUA reply and falls back to DOM heuristics.

### Data Flow
- UI (`ui_streamlit.py`) collects: profile, criteria, template → builds services with `build_services()` → constructs `AutonomousFlow` → runs with selected mode and safety flags.
- `AutonomousFlow`: open YC URL → loop up to `limit` → stop gate → click profile → read text → dedupe (SQLite) → evaluate (`EvaluateProfile`: decision adapter + renderer) → log → auto-send via `SendMessage` when allowed → verify → results summary + event emission.
- Logging: JSONL via `JSONLLogger` wrapped with `LoggerWithStamps` for prompt/rubric versions.
- Quota: File-based counter (default) or SQLite daily/weekly when enabled.

### Diagrams
- See `ARCHITECTURE_MERMAID.md` for up-to-date sequence, flow, and state diagrams aligned with code.

## Gaps vs Claims
- Model auto-resolution and GPT-5 claims: resolver exists but unused; documentation should permit GPT-4 family fallback.
- Auto-login/singleton: implemented in async adapter, not default; either wire it via DI or soften claims in docs.
- Async ergonomics: CUA OpenAI calls in async context are synchronous; run in executor to avoid event loop blocking.

