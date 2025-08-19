Testing & Quality

Philosophy
- Start with targeted unit tests around tools and helpers; add lightweight integration tests for the Playwright adapter. Keep end‑to‑end manual and supervised initially.

Tests (MVP)
- Unit: quota_guard counter logic; message templating; decision function (yes/no + rationale consistency); scoring heuristics.
- Integration: (next) Computer adapter methods (screenshot, click, type) using a local test page.
- Manual E2E: Runbook in Operations doc; verify decision quality and quota behavior.

Static Analysis
- Lint: `ruff` (format + lint rules)
- Types: `mypy` with strictness on internal modules

CI Hooks (optional initially)
- `pre-commit` with ruff, mypy, and secret‑scan.
- GitHub Actions to run lint + tests on PRs.

Coding Standards
- Small modules/functions; clear names; no secrets in logs.
- Avoid brittle selectors; prefer visible text/positions supervised by the agent.
