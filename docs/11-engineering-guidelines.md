Engineering Guidelines (DDD, Clean Code, TDD)

Principles
- DDD: Separate domain, application, infrastructure, and interface layers; keep domain pure.
- SOLID/DRY/Clean: Small, cohesive modules; explicit dependencies; no duplication.
- TDD: Write failing unit tests first for domain/application; iterate to green; refactor.
- Ports & Adapters: Define clear contracts; swap implementations (CUA/Playwright, decision modes) without touching orchestrators.

Layering
- Domain: entities/value objects (UserProfile, MatchCriteria, Decision), domain services (scoring/extraction), framework‑agnostic.
- Application: use cases/orchestrators (DiscoverProfiles, EvaluateAndMessage, ProcessBatch); ports (interfaces) that infra implements.
- Infrastructure: adapters/clients (Anthropic/OpenAI CUA, Playwright fallback, SQLite repos, JSONL logger, decision adapters, message renderer).
- Interface: Streamlit UI and CLI; DI container/factories to compose the app per env.

Dependencies
- Domain → none
- Application → Domain
- Infrastructure → Application + Domain (implements ports)
- Interface → Application (invokes use cases)

Ports (Interfaces)
- ComputerUsePort: `open(url)`, `find_click(locator|text|role)`, `read_text(selector|region)`, `fill(selector,text)`, `press_send()`, `verify_sent()`, `close()`
- DecisionPort: `evaluate(profile_text, criteria) -> DecisionResult`
- QuotaPort: `check_remaining() -> int`, `decrement()`, `reset()`
- SeenRepo: `is_duplicate(hash) -> bool`, `mark_seen(hash)`
- LoggerPort: `log_event(event_type, data)`
- StopController: `should_stop() -> bool`

Adapters
- CUA (PRIMARY): `AnthropicCUAAdapter` now; `OpenAICUAAdapter` when available.
- Browser (FALLBACK): `PlaywrightBrowserAdapter` if CUA unavailable.
- Decision: Advisor (LLM-only), Rubric (deterministic), Hybrid (combined α).
- Storage: SQLite quota/seen; JSONL logger.
- Messaging: template renderer with safety clamps and length limits.

Testing Strategy
- Unit: decision math, hard rules, template rendering, STOP/quotas/pacing/dedupe.
- Contract: fake `ComputerUsePort` and assert call sequences and invariants.
- Integration: optional local replayer and Playwright fallback smoke tests; no external network in CI.

Config & DI
- All flags via `.env` and UI: `DECISION_MODE`, `THRESHOLD`, `ALPHA`, `STRICT_RULES`, `ENABLE_CUA`, `CUA_PROVIDER`, `ENABLE_PLAYWRIGHT_FALLBACK`.
- Repo‑scoped caches only (`UV_CACHE_DIR`, `XDG_CACHE_HOME`, `PLAYWRIGHT_BROWSERS_PATH`).
- Compose adapters based on config; keep constructors small and explicit.

Logging & Versioning
- JSONL events: `decision`, `sent`, `stopped`, `model_usage` with `prompt_ver`, `rubric_ver`, `criteria_hash`.
- Refuse to send unless `verify_sent()` succeeds; log `sent{ok:true,mode}` only on verification.

Refactoring Policy
- Prefer small, surgical patches; keep public contracts stable.
- Avoid cross‑cutting refactors; upgrade modules incrementally under tests.
