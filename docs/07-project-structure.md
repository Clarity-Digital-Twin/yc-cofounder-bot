# 07 — Project Structure

**Status:** Draft v0.2 (2025-08-20)  
**Owner:** YC Matcher Team  
**Related:** [03-architecture.md] · [06-dev-environment.md] · [08-testing-quality.md]

**Goal:** Make the repo's layout, responsibilities, and run commands unambiguous so new contributors can ship safely without breaking the CUA-first automation flow.

## Top-Level Layout

```
yc-cofounder-bot/
├── docs/                       # Product, architecture, ops, UI, prompts
│   ├── 01-product-brief.md
│   ├── 02-scope-and-requirements.md
│   ├── 03-architecture.md
│   ├── 04-implementation-plan.md
│   ├── 05-operations-and-safety.md
│   ├── 06-dev-environment.md
│   ├── 07-project-structure.md   <-- this file
│   ├── 08-testing-quality.md
│   ├── 09-roadmap.md
│   ├── 10-ui-reference.md
│   ├── 11-engineering-guidelines.md
│   └── 12-prompts-and-rubric.md
├── Makefile                    # repo-scoped env + convenience targets
├── pyproject.toml              # deps + tooling config
├── .env.example                # required env keys
├── MODEL_SELECTION.md          # how to pick/upgrade CUA & decision models
├── OPENAI_COMPUTER_USE_TRUTH.md # package/import facts for CUA (agents)
├── .uv_cache/                  # repo-local UV cache (do not commit)
├── .cache/                     # repo-local XDG cache (do not commit)
├── .ms-playwright/             # repo-local browsers (optional)
├── .mplconfig/                 # repo-local matplotlib config
├── .home/                      # repo-local HOME for Streamlit
├── .runs/                      # runtime state (created at run time)
│   ├── events.jsonl            # append-only audit log
│   ├── seen.sqlite             # dedupe DB
│   ├── quota.sqlite            # daily/weekly counters
│   └── stop.flag               # STOP kill switch (presence-based)
├── src/
│   └── yc_matcher/
│       ├── domain/             # pure types + invariants (no IO)
│       │   ├── entities.py     # Profile, Criteria, Decision, Template
│       │   ├── services.py     # business logic
│       │   └── __init__.py
│       ├── application/        # use-cases orchestrating ports
│       │   ├── ports.py        # BrowserPort, DecisionPort, LoggerPort, QuotaPort, SeenRepo
│       │   ├── schema.py       # DTOs and schemas
│       │   ├── gating.py       # decision gating logic
│       │   ├── use_cases.py    # Evaluate, ProcessCandidate, Send
│       │   └── __init__.py
│       ├── infrastructure/     # adapters (IO, SDKs)
│       │   ├── openai_cua_browser.py   # PRIMARY: CUA planner (Responses API) + Playwright executor
│       │   ├── browser_playwright.py   # FALLBACK: PlaywrightBrowser
│       │   ├── openai_decision.py      # OpenAI decision adapter
│       │   ├── local_decision.py       # local/mock decision adapter
│       │   ├── sqlite_repo.py          # seen/quota base implementation
│       │   ├── sqlite_quota.py         # quota tracking
│       │   ├── sqlite_progress.py      # progress tracking
│       │   ├── jsonl_logger.py         # events.jsonl emitter
│       │   ├── logger_stamped.py       # stamped logger wrapper
│       │   ├── stop_flag.py            # STOP flag controller
│       │   ├── templates.py            # message template rendering
│       │   ├── template_loader.py      # template file loading
│       │   ├── normalize.py            # profile normalization
│       │   ├── click_helpers.py        # UI click helpers
│       │   ├── quota.py                # quota abstractions
│       │   ├── storage.py              # storage utilities
│       │   └── __init__.py
│       ├── interface/          # DI + entry points (web/cli)
│       │   ├── di.py           # dependency injection
│       │   ├── web/
│       │   │   └── ui_streamlit.py     # 3-input control panel (CUA-first)
│       │   ├── cli/
│       │   │   ├── check_cua.py        # confirms CUA model access/availability
│       │   │   └── run.py              # CLI runner (optional)
│       │   └── __init__.py
│       └── config.py           # configuration loading
└── tests/
    ├── unit/                   # pure function/class tests
    │   ├── test_decision_math.py
    │   ├── test_gating.py
    │   ├── test_logger_jsonl.py
    │   ├── test_logger_stamps.py
    │   ├── test_openai_decision_adapter.py
    │   ├── test_quota_simple.py
    │   ├── test_template_render.py
    │   └── test_use_cases.py
    ├── integration/            # browser adapter smoke + CUA pipeline
    │   ├── test_browser_smoke.py       # marked "integration"; skip if no Playwright
    │   └── test_playwright_fallback.py
    └── conftest.py

```

## Invariants

- **CUA is primary** (`OpenAICUABrowser`); **Playwright** only runs if `ENABLE_PLAYWRIGHT_FALLBACK=1` *and* CUA init/action fails, or if you explicitly force Playwright via `ENABLE_PLAYWRIGHT=1`
- No code writes to `$HOME` or `~/.cache`. All caches are under the repo
- **Three inputs only**: *Your Profile*, *Match Criteria*, *Message Template*. No "paste the candidate profile" path

## Ports & Adapters (File-Level Contracts)

### Application Ports (`src/yc_matcher/application/ports.py`)

- `BrowserPort`: `open(url)`, `read_profile_text() -> str`, `focus_message_box()`, `fill_message(text)`, `click_send()`, `verify_sent() -> bool`, `close()`
- `DecisionPort`: advisor/rubric/hybrid scoring interface returning a normalized decision payload (`decision`, `scores`, `rationale`)
- `LoggerPort`: `emit(dict) -> None` (JSONL lines)
- `QuotaPort`: `allow() -> bool`, `increment() -> None`
- `SeenRepo`: `seen(key) -> bool`, `mark(key) -> None`

### Primary Adapter

**`openai_cua_browser.py`** → `OpenAICUABrowser` (CUA planner + Playwright executor):

Uses OpenAI Responses API with the `computer_use` tool to plan actions from screenshots; executes actions locally with Playwright; chains turns via `previous_response_id` and `computer_call_output`.

### Fallback Adapter

**`browser_playwright.py`** → `PlaywrightBrowser`
- Same `BrowserPort` contract; selector heuristics for YC
- Repo-local browsers under `.ms-playwright/`

## Interface Layer

**`interface/di.py`** wires:
- `OpenAICUABrowser` if `ENABLE_CUA=1`
- else `PlaywrightBrowser` if `ENABLE_PLAYWRIGHT=1`
- else a null browser (safe no-op)
- If CUA errors and `ENABLE_PLAYWRIGHT_FALLBACK=1`, fall back to Playwright-only **for that run**

**Streamlit UI (`interface/web/ui_streamlit.py`)** exposes exactly three inputs (profile, criteria, template), plus controls:
- **Run / STOP** toggle, **Decision Mode**, **Threshold**, **Shadow Mode**
- **Approve & Send** button if Advisor (HIL) mode is selected
- Live tail of `events.jsonl`

## Configuration (env)

```bash
# Engines
ENABLE_CUA=1
ENABLE_PLAYWRIGHT_FALLBACK=1
ENABLE_PLAYWRIGHT=0

# OpenAI
OPENAI_API_KEY=sk-...
CUA_MODEL=<your-computer-use-model>   # from Models endpoint
CUA_TEMPERATURE=0.3
CUA_MAX_TOKENS=1200

# Decision
DECISION_MODE=hybrid                  # advisor|rubric|hybrid
OPENAI_DECISION_MODEL=<best-llm>      # for Advisor/Hybrid
THRESHOLD=0.72
ALPHA=0.50

# Runtime & Pacing
YC_MATCH_URL=https://www.startupschool.org/cofounder-matching
PACE_MIN_SECONDS=45
DAILY_QUOTA=25
WEEKLY_QUOTA=120
SHADOW_MODE=0
```

**Repo-Scoped Caches (enforced in Makefile)**
- `UV_CACHE_DIR=.uv_cache`
- `XDG_CACHE_HOME=.cache`
- `PLAYWRIGHT_BROWSERS_PATH=.ms-playwright`
- `MPLCONFIGDIR=.mplconfig`

## Make Targets (Standard Runbook)

- `make doctor` – prints repo-scoped paths (no `$HOME`)
- `make verify` – ruff + mypy + unit tests
- `make browsers` – (optional) `python -m playwright install chromium` into `.ms-playwright/`
- `PLAYWRIGHT_HEADLESS=1 make test-int` – integration suite (skips if playwright not installed)
- `make run` – runs Streamlit UI (`ui_streamlit.py`) with repo-scoped env
- `make check-cua` – verify OpenAI Computer Use access

## Tests

```
tests/
├── unit/...                    # fast, no external dependencies
├── integration/
│   └── test_browser_smoke.py  # marked "integration"; uses Playwright; skip if missing
└── conftest.py                 # shared fixtures
```

### Markers
- Use `@pytest.mark.integration` for browser-dependent tests
- Never fail CI if Playwright is unavailable—**skip** cleanly

## Runtime Artifacts

- `events.jsonl` – append-only JSONL (decision, sent, model_usage, quota, stop, error)
- `.runs/seen.sqlite` – dedupe by stable key (e.g., `hash(profile_url + name)`)
- `.runs/quota.sqlite` – daily/weekly counters
- `.runs/stop.flag` – presence halts new actions

### Canonical "sent" Event
```json
{"event":"sent","ok":true,"mode":"auto","verified":true,"chars":312}
```

## Conventions

- **Naming:** `snake_case` files, `CapWords` classes, `lower_snake` env keys in code
- **Imports:** Prefer Responses API directly for CUA; Agents Runner (`from agents import ...`) is optional
- **Logging:** only via JSONL logger; no `print` in adapters/use-cases
- **Type hints & docstrings:** required in `domain/` and `application/`

## File Responsibilities

### Domain Layer
- `entities.py`: Core domain models (Profile, Criteria, Decision)
- `services.py`: Business logic and rules

### Application Layer
- `ports.py`: Abstract interfaces for external services
- `use_cases.py`: Orchestration logic (evaluate, send, audit)
- `schema.py`: Data transfer objects and validation schemas
- `gating.py`: Decision gating and threshold logic

### Infrastructure Layer
- `openai_cua_browser.py`: PRIMARY browser automation via OpenAI Computer Use
- `browser_playwright.py`: FALLBACK browser automation
- `openai_decision.py`: OpenAI-based decision making
- `sqlite_*.py`: SQLite persistence (quota, seen, progress)
- `jsonl_logger.py`: Event logging to JSONL
- `templates.py`: Message template rendering

### Interface Layer
- `di.py`: Dependency injection and adapter wiring
- `ui_streamlit.py`: Web UI with 3-input control panel
- `check_cua.py`: CUA availability checker
- `run.py`: CLI runner

## Definition of Done (Doc 07)

- The file tree, env keys, adapters, and Make targets match this document
- The **CUA-first** stance and **Playwright fallback** are unmistakable
- Tests can be discovered with or without Playwright installed (skip vs fail is correct)
- Every other doc (01–06, 08–12) references the **same env keys** and **same adapter names**

## Key Differences from Initial Proposal

The actual implementation uses:
- `yc_matcher` namespace instead of `app`
- Flatter structure in some areas (e.g., decision adapters directly in infrastructure/)
- More granular infrastructure modules (separate files for different concerns)
- Additional utility modules (normalize.py, click_helpers.py, etc.)

**Result:** With this Doc 07, the repo's structure is fully synchronized with the product we're actually building: **3 inputs → CUA-first autonomy → safe fallback → auditable events**.
