Testing & Quality

Philosophy
- TDD for domain/application: write failing unit tests first, iterate to green, then refactor.
- Keep adapters behind ports; prefer contract tests with fakes over fragile E2E.
- CI-local: no external network; integration is opt-in and uses a local replayer/test page.

Test Suites
- Unit (Domain/Application)
  - Decision math: Advisor (LLM-only contract), Rubric (deterministic scoring), Hybrid (α·llm_confidence + (1−α)·rubric_score).
  - Hard rules gates (STRICT_RULES=1): must_be_technical, commitment_available, location_acceptable.
  - Template rendering: variables `{name},{tech},{hook},{city},{why_match}`; clamps and length limits.
  - Controls: STOP flag behavior; quotas; pacing; dedupe pre-checks.
- Contract (Ports)
  - `ComputerUsePort` via fakes: open→find_click→read_text→fill→press_send→verify_sent; assert call order and invariants.
  - LoggerPort emits structured JSON events; schema sanity.
- Integration (Opt-in)
  - Playwright fallback smoke against local static page (no real YC site).
  - Adapter parity where feasible.

Gates & Commands
- Lint: `make lint` (ruff)
- Format: `make format` (ruff)
- Types: `make typecheck` (mypy strict)
- Tests: `make test` (pytest)
- All gates: `make verify` (lint + type + test)

Data & Logs
- JSONL events: `decision`, `sent`, `stopped`, `model_usage`; include `prompt_ver`, `rubric_ver`, `criteria_hash`.
- Repo-scoped caches only; no writes to `$HOME`.

Quality Policies
- Small, surgical patches; avoid broad refactors.
- Fail closed: if extraction uncertain or rules fail, do not send.
- Deterministic unit tests; seeded randomness if any.
- No secrets in logs; redact PII when `PII_REDACTION=1`.
