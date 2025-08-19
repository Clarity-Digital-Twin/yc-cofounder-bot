Architecture

Principles
- Keep orchestration minimal; leverage OpenAI’s Computer Use with a thin Playwright adapter.
- Prefer human‑visible, supervised operation; no hidden background actions.
- Use simple local storage (SQLite/JSON) only where it adds clear value.
 - Adopt DDD layering: Domain (pure) → Application (use cases) → Infrastructure (adapters) → Interface (UI/CLI).

High‑Level Components (mapped to DDD layers)
- Domain:
  - Entities/VOs: Criteria, Profile, Decision, Score.
  - Domain Services: ScoringService (Strategy pattern for weights/rules).
- Application:
  - Use Cases: EvaluateProfile, SendMessage, ProcessCandidate.
  - Ports: DecisionPort, ScoringPort, MessagePort, QuotaPort, SeenRepo, LoggerPort, BrowserPort.
- Infrastructure:
  - OpenAIDecisionAdapter (Facade/Adapter) implements DecisionPort.
  - SQLiteSeenRepo implements SeenRepo.
  - JSONLLogger implements LoggerPort.
  - PlaywrightBrowserAdapter implements BrowserPort with `click_by_text` + retries.
  - TemplateRenderer implements MessagePort with clamps and safety.
- Interface:
  - Streamlit UI and CLI; DI factories to wire ports to use cases.
- Config & Secrets:
  - `.env` for OPENAI_API_KEY and URL; app args for run‑time overrides.
- Persistence:
  - SQLite: `seen_profiles` (hash, ts), `runs`, `events`; session logs and dedupe.

Data Flow (MVP Semi‑Auto)
1) Operator enters Criteria + Template; headful browser opens target URL; operator logs in.
2) Agent navigates list → clicks “View profile” (visible text), reads profile.
3) Decision Service parses profile → schema output; Rubric gates YES/NO; model provides rationale/draft.
4) UI shows decision; on approval, `quota_guard` → focus right panel → slot & clamp draft → click “Send” or “Skip”.
5) Logger writes JSONL; SQLite updates seen/dedupe; stop at quota or no more candidates.

Key Configs
- Model: `computer-use-preview` (OpenAI Responses/Agents SDK backend).
- Display: 1280×800 or similar to reduce screenshot size and keep layout stable.
- Timeouts: per‑step wait 0.5–2s; max overall runtime configurable.
- Quota: integer per run; default 5.

Security & Privacy
- No credentials in prompts.
- Local `.env`, not committed; recommend `pre-commit` to block secrets.

Extensibility
- Add a Streamlit UI by wrapping the run() coroutine and streaming logs.
- Add per‑site adapters if needed later; keep the Computer interface stable.
