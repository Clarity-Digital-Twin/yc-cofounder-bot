# 08 — Testing & Quality

**Status:** Draft v0.2 (2025-08-20)  
**Owner:** QA / Eng  
**Related:** [02-scope-and-requirements.md] · [03-architecture.md] · [06-dev-environment.md] · [11-engineering-guidelines.md]

---

## 1) Quality Goals

- **Correctness:** All Functional (FR-xx) and Non-Functional (NFR-xx) requirements pass with traceable tests
- **Safety:** Never send messages when STOP, quotas, or Shadow mode forbid it
- **Hermeticity:** No tests write to `$HOME`; all caches and artifacts are repo-local
- **Stability:** Integration tests are **non-flaky**; Playwright fallbacks covered headless
- **Observability:** Every run yields a parseable `events.jsonl`, stable schema, and junit/coverage artifacts

---

## 2) Test Pyramid

### Unit Tests (fast, hermetic)
- Pure domain logic (scoring, templating, dedupe keys)
- Rubric computations; Hybrid blending `final = α*advisor + (1-α)*rubric`
- Log/event schema emission
- STOP flag behavior, quotas, pacing

### Contract Tests (ports)
- `ComputerUsePort` (CUA planner) — stub Responses API `computer_call`/`computer_call_output` and assert Playwright execution
- `BrowserPort` (Playwright-only fallback) — stub Playwright
- `DecisionPort` — advisor/hybrid expectations with deterministic prompts
- LoggerPort emits structured JSON events; schema sanity

### Integration Tests (headless, no live YC)
- End-to-end **on a local fixture page**: open → read → decide → draft → (conditionally) **simulate send** → verify
- Playwright **headless** smoke validates selectors and adapter contract
- SQLite persistence (seen, quota, progress)

### HIL Smoke (optional but recommended)
- With real browser (CUA or Playwright), manual login, and live YC page
- Limited canary flow verifies selectors and site drift handling

---

## 3) Traceability (IDs from Doc 02)

| Layer          | Test ID         | Test File                        | Covers                                              |
|----------------|-----------------|----------------------------------|-----------------------------------------------------|
| Unit           | UNIT-DEC-01     | test_gated_decision.py          | FR-06/07/08/09 (Advisor/Rubric/Hybrid + threshold) |
| Unit           | UNIT-LOG-01     | test_logger_jsonl.py            | FR-18/19/20 (events schema, `sent` format)         |
| Unit           | UNIT-THRESH-01  | test_scoring.py                 | FR-09 (threshold gates auto-send)                  |
| Unit           | UNIT-TEMPLATE-01| test_templates_renderer.py      | FR-11 (template rendering with placeholders)       |
| Unit           | UNIT-STOP-01    | test_stop_flag.py               | FR-14 (STOP flag behavior)                         |
| Unit           | UNIT-QUOTA-01   | test_sqlite_quota.py            | FR-15 (quota management)                           |
| Contract       | PORT-CUA-01     | test_openai_decision_adapter.py | CUA adapter contract                               |
| Contract       | PORT-BR-01      | test_browser_port.py            | Playwright fallback contract parity                |
| Integration    | INT-NAV-CUA-01  | test_browser_port.py            | FR-01/02 (open listing, iterate profiles)          |
| Integration    | INT-EXTRACT-01  | test_normalizer.py              | FR-04/05 (extract fields from text)                |
| Integration    | INT-MSG-01      | test_process_candidate.py       | FR-11/12 (template render, conditional send)       |
| Integration    | INT-VERIFY-01   | test_send_verify.py             | FR-13 (verify sent; single retry)                  |
| Integration    | INT-STOP-01     | test_process_candidate_stop.py  | FR-14 (STOP halts ≤2s)                            |
| Integration    | INT-QUOTA-01    | test_sqlite_quota.py            | FR-15 (daily/weekly quota enforce)                 |
| Integration    | INT-SHADOW-01   | test_use_cases.py               | FR-16 (evaluate only, never send)                  |
| Integration    | INT-FALLBACK-01 | test_browser_port.py            | FR-17 (force CUA fail → Playwright path)           |
| Integration    | INT-LOCAL-01    | test_marker_smoke.py            | NFR-06 (no `$HOME` writes)                         |

**Acceptance Criteria mapping:** AC-01..AC-07 map to the respective INT tests above.

---

## 4) Commands & Targets

> All commands must be run from repo root. **No `$HOME` writes**; Makefile enforces repo-local caches.

### Core Commands
- **Static + unit:**  
  `make verify` → Ruff (lint) + Mypy (types) + Pytest (unit)
- **Integration (headless):**  
  `PLAYWRIGHT_HEADLESS=1 make test-int`
- **Playwright browsers (local cache):**  
  `make browsers`
- **HIL smoke (visible):**  
  ```bash
  export ENABLE_PLAYWRIGHT=1  # or ENABLE_CUA=1 if testing CUA
  uv run streamlit run -m yc_matcher.interface.web.ui_streamlit
  ```
- **CUA readiness probe:**  
  `make check-cua` *(initializes `agents` import; prints model availability hints)*

### Environment (enforced in Makefile / CI)
```bash
UV_CACHE_DIR=.uv_cache
XDG_CACHE_HOME=.cache
PLAYWRIGHT_BROWSERS_PATH=.ms-playwright
MPLCONFIGDIR=.mplconfig
```

---

## 5) Fixtures & Hermeticity

### Local HTML Fixtures
- For integration tests (no network): listing page with tiles, profile page with message box
- Located in `tests/fixtures/` or generated dynamically

### CUA Stubs
For contract tests:
- Stub the Responses API and provide deterministic `computer_call` actions
- Mock `client.responses.create()` to return expected response structures with reasoning/message items

### Ephemeral State
For tests:
- Use `tmp_path` to create `.runs-test/seen.sqlite`, `.runs-test/quota.sqlite`, and `events-test.jsonl`
- **Never** write to `.runs/` in CI; local dev can opt-in with explicit flags

### Random Seeds
Set `PYTHONHASHSEED` and test-level seeds for reproducibility

---

## 6) Coverage & Quality Gates

### Coverage Goals
- **Line Coverage:** ≥ 85%
- **Branch Coverage:** ≥ 70%
- **Domain & Application packages:** ≥ 90% line coverage

### Schema Lock
Event fields (`event`, `ok`, `mode`, `verified`, `retry`, `provider`, `model`, ...) must be asserted in `UNIT-LOG-01`

### Zero-Test Guard
The integration suite includes a marker smoke test to prevent "0 tests collected"

### Artifacts (CI)
- `reports/junit.xml` (pytest)
- `reports/coverage.xml` + `htmlcov/`
- `artifacts/events-test.jsonl` (sample)
- `artifacts/playwright-traces/` (if enabled)

---

## 7) Flake Prevention & Triage

- **Headless Playwright:** Use deterministic timeouts and explicit waits
- **Site-dependent tests:** Mark as HIL-only; keep CI fully offline
- **Flaky marker:** Use `@pytest.mark.flaky(reruns=1, reruns_delay=1)` **only** where timing varies
- **Selector patches:** A failure on INT-FALLBACK-01 mandates a **selector patch** in the fallback adapter

---

## 8) Safety Assertions

### STOP Precedence (FR-14)
Assert no `sent` events after STOP file created mid-run

### Quota Precedence (FR-15)
With `DAILY_QUOTA=1`, second eligible profile **must not** send; log `quota_exceeded`

### Shadow Mode (FR-16)
Assert decisions logged, **no** `sent` events

### Dedupe (FR-10/FR-20)
Re-run over same listing yields **no** duplicate sends; `seen` grows only once per key

---

## 9) Example Assertions

### Events Schema
```python
event = jsonl[-1]
assert event["event"] in {"decision", "sent", "error", "stop", "quota"}
if event["event"] == "sent":
    assert event["ok"] is True
    assert event["mode"] in ["auto", "manual"]
    assert event["verified"] in (True, False)
```

### No $HOME Writes (NFR-06)
```python
for p in walked_paths:
    assert not str(p).startswith(os.path.expanduser("~")), "Unexpected write to $HOME"
```

### Hybrid Score
```python
final = alpha * advisor_conf + (1 - alpha) * rubric_score
assert 0.0 <= final <= 1.0
```

### Template Rendering
```python
rendered = template.render(first_name="John", why_match="ML expertise")
assert "{" not in rendered  # No unresolved placeholders
assert len(rendered) <= 500  # Character limit
```

---

## 10) Test Data (Minimal)

### Your Profile
Dr. Jung profile markdown (short sample)

### Criteria
- Must-haves: domain/stack/timezone
- Should-haves: stage, industry

### Template
```
Hey {first_name}, loved your {their_highlight}. 
I'm a {my_context} ... {cta}
```

---

## 11) How to Run Locally (Happy Path)

```bash
# One-time setup
mkdir -p .uv_cache .cache .ms-playwright .mplconfig .runs

# Quality loop
make verify

# Install browsers (if using Playwright fallback)
make browsers

# Integration headless
PLAYWRIGHT_HEADLESS=1 make test-int

# Optional HIL (visible)
export ENABLE_PLAYWRIGHT=1
uv run streamlit run -m yc_matcher.interface.web.ui_streamlit
```

**Expected:** Integration lane green; if HIL is run and you approve a **YES**, an event
`{"event":"sent","ok":true,"mode":"auto","verified":true}` appears in `events.jsonl`.

---

## 12) Known Pitfalls & Fixes

### Permission Denied
Under `/home/*` or `~/.cache/*` → Use repo-scoped caches (see env above)

### Missing Playwright Binaries
`make browsers` (or set `PLAYWRIGHT_CHANNEL` to use system browser)

### CUA Not Available
Verify `OPENAI_API_KEY`, `CUA_MODEL`, and account tier; run `make check-cua`

### Selectors Drift on YC
Add a **targeted fallback** for the exact visible text (button/link) in the Playwright adapter

---

## 13) Exit Criteria for "Green"

- `make verify` is green (ruff 0, mypy 0, unit pass)
- `PLAYWRIGHT_HEADLESS=1 make test-int` passes (integration lane)
- Optional HIL flow works; visible approve/send produces canonical `sent` event
- No writes to `$HOME`; Makefile doctor prints repo-local cache paths

---

## 14) Actual Test Files

### Unit Tests (`tests/unit/`)
- `test_gated_decision.py` - Decision gating logic
- `test_logger_jsonl.py` - JSONL event logging
- `test_logger_stamps.py` - Stamped logger wrapper
- `test_normalizer.py` - Profile text normalization
- `test_openai_decision_adapter.py` - OpenAI decision adapter
- `test_process_candidate.py` - Candidate processing flow
- `test_process_candidate_stop.py` - STOP flag behavior
- `test_schema.py` - Data schemas and validation
- `test_scoring.py` - Rubric and hybrid scoring
- `test_send_verify.py` - Send verification logic
- `test_sqlite_progress.py` - Progress tracking
- `test_sqlite_quota.py` - Quota management
- `test_stop_flag.py` - STOP flag controller
- `test_templates_renderer.py` - Template rendering
- `test_use_cases.py` - Use case orchestration

### Integration Tests (`tests/integration/`)
- `test_browser_port.py` - Browser port contract
- `test_marker_smoke.py` - Smoke test marker
- `test_sqlite_repo.py` - SQLite persistence

### E2E Tests (`tests/e2e/`)
- Reserved for future live site tests (currently empty)
