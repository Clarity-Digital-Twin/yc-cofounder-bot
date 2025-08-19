Testing & Quality

Philosophy
- Start with targeted unit tests around tools and helpers; add lightweight integration tests for the Playwright adapter. Keep end‑to‑end manual and supervised initially.
 - Practice TDD for domain/application code: write failing tests for use cases and domain services, then implement.

Tests (MVP)
- Unit (Domain/Application): schema validation (strict); scoring weights/threshold; use cases (EvaluateProfile/SendMessage) against mocked ports; template clamps.
- Integration (Infrastructure): OpenAI decision adapter via stubbed responses; Playwright adapter against a local test page; SQLite repo R/W; JSONL logger appends.
- Manual E2E (Shadow Mode): decisions vs human labels; calibrate rubric before enabling sends.

Static Analysis
- Lint: `ruff` (format + lint rules)
- Types: `mypy` with strictness on internal modules

CI Hooks (optional initially)
- `pre-commit` with ruff, mypy, and secret‑scan.
- GitHub Actions to run lint + tests on PRs.
 - Test matrix: OSes (macOS/Windows/Linux) and Python versions (3.11/3.12) when stable.

Coding Standards
- Small modules/functions; clear names; no secrets in logs.
- Avoid brittle selectors; prefer visible text/positions supervised by the agent.
 - Fail closed on schema parse errors; surface actionable messages to user.
