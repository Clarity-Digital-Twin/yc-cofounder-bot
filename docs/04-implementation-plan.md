# 04 — Implementation Plan

**Status:** Draft v0.2 (2025-08-20)  
**Owner:** YC Matcher Team  
**Related:** [01-product-brief.md] · [02-scope-and-requirements.md] · [03-architecture.md] · [10-ui-reference.md]

This plan maps directly to the SSOT: CUA+Playwright work together (CUA analyzes, Playwright executes), three decision modes, STOP/quotas/dedupe, single-page UI.

## Milestones

### M0 — Project Hygiene (Day 0)
- [ ] Repo-scoped caches only: `.uv_cache`, `.cache`, `.ms-playwright`, `.mplconfig`, `.runs`
- [ ] Make targets: `doctor`, `verify`, `browsers`, `test-int`, `run`, `check-cua`
- [ ] CI: run `make verify` on PRs (ruff, mypy, pytest)

**Acceptance:**
- `make doctor` shows only repo-local caches
- `make verify` green

### M1 — Core CUA + Modes + Fallback (Week 1)
- [ ] Define ports (contracts): `ComputerUsePort`, `DecisionPort`, `QuotaPort`, `SeenRepo`, `LoggerPort`, `StopController`
- [ ] Implement OpenAI CUA adapter with integrated Playwright (CUA analyzes, Playwright executes)
- [ ] Add screenshot loop: Playwright captures → CUA analyzes → suggests action → Playwright executes
- [ ] Implement computer_call execution via Playwright (click, type, scroll based on CUA suggestions)
- [ ] Wire Playwright-only mode (no CUA) as fallback behind flag (`ENABLE_PLAYWRIGHT_FALLBACK=1`)
- [ ] Implement decision modes: Advisor, Rubric, Hybrid (shared `DecisionResult` schema)
- [ ] Streamlit single-page UI: 3 inputs, mode selector, threshold/alpha, strict-rules toggle, provider selector, RUN/STOP, quotas, live events
- [ ] Emit JSONL events: `decision`, `sent`, `stopped`, `model_usage`

**Acceptance:**
- Unit tests for each port + adapter stubs
- `make test-int` has at least one CUA smoke and one Playwright smoke
- JSONL events emitted in canonical shape
- Advisor/Rubric/Hybrid modes selectable; decisions logged with versions

### M2 — Robustness & Safety (Week 2)
- [ ] STOP flag checks before navigation and before send; state preservation
- [ ] Quotas (SQLite): daily/weekly caps; decrement on verified `sent`
- [ ] Deduplication (SQLite): profile hash check pre-evaluation
- [ ] Pacing (`SEND_DELAY_MS`) and exponential backoff
- [ ] Shadow Mode (evaluate-only) and optional HIL (`REQUIRE_APPROVAL=1`)
- [ ] Cost tracking and token caps; provider status indicator

**Acceptance:**
- `events.jsonl` captures: `decision`, `sent` (`ok: true`, `mode: "auto"`), `model_usage`, `quota`, `stop`
- `.runs/seen.sqlite` updates after each send
- STOP flag respected (`.runs/stop.flag`)
- Verified `sent{ok:true,mode}` after successful send; quotas decrement

### M3 — CUA Enhancement & Testing (Week 3)
- [ ] Add session management and context tracking
- [ ] Implement retry logic with exponential backoff
- [ ] Add token optimization (context truncation)
- [ ] Full integration testing with YC site
- [ ] Contract tests for all CUA methods
- [ ] Provider dropdown and status in UI

**Acceptance:**
- OpenAI adapter fully implemented and configurable
- Parity tests between CUA and Playwright adapters
- Provider status shows CUA connected/fallback active

### M4 — Ranking, Analytics, and UX Polish (Week 4)
- [ ] Ranking view and decision distribution charts
- [ ] Prompt/rubric versioning surfaced in UI; criteria hash
- [ ] Export CSV and simple analytics (cost, profiles/hour, success/failure)
- [ ] Canary & rollback documentation

**Acceptance:**
- Analytics widgets functional
- CSV export works
- Versioning visible in UI
- Recoverable failures logged with context

## Configuration (env)

```bash
# Enable engines
ENABLE_CUA=1                        # Primary: OpenAI Computer Use
ENABLE_PLAYWRIGHT_FALLBACK=1        # Only used if CUA fails/unavailable
ENABLE_PLAYWRIGHT=0                 # Force Playwright (testing only)

# OpenAI
OPENAI_API_KEY=sk-...
CUA_MODEL=<your-computer-use-model> # from Models endpoint
CUA_TEMPERATURE=0.3
CUA_MAX_TOKENS=1200

# Decision
DECISION_MODE=hybrid                # advisor | rubric | hybrid
OPENAI_DECISION_MODEL=<best-reasoning-llm>
ALPHA=0.30                          # hybrid weight for Advisor
THRESHOLD=0.72                      # auto-send threshold
STRICT_RULES=0                      # when 1, rubric gates hard-fail
REQUIRE_APPROVAL=0                  # when 1, HIL approval required

# Targets
YC_MATCH_URL="https://www.startupschool.org/cofounder-matching"

# Safety & Limits
DAILY_QUOTA=25
WEEKLY_QUOTA=120
SEND_DELAY_MS=5000
SHADOW_MODE=0                       # 1 = evaluate-only, never send

# Repo-scoped caches
UV_CACHE_DIR=.uv_cache
XDG_CACHE_HOME=.cache
PLAYWRIGHT_BROWSERS_PATH=.ms-playwright
MPLCONFIGDIR=.mplconfig
```

## Testing Strategy

### Static/Unit
- `ruff` clean; `mypy` strict on `src/yc_matcher/**`
- Unit tests for: decision math (advisor, rubric, hybrid), hard rules, template rendering, STOP, quotas, pacing, dedupe

### Contract
- `ComputerUsePort` with fakes; assert call sequences
- No real browsing in contract tests

### Integration
- `PLAYWRIGHT_HEADLESS=1 make test-int` validates fallback adapter
- `ENABLE_CUA=1` path: mock CUA with fake screen/act loop
- Local HTML replayer page for Playwright smoke tests

### E2E (manual/HIL)
- `make run` (Streamlit) → login → RUN (Shadow or Auto)
- Verify artifacts:
  - `events.jsonl` contains `decision` then `sent` (`ok:true`, `mode:"auto"`)
  - `.runs/seen.sqlite` upserts
  - `.runs/quota.sqlite` updates when quota enabled
  - `.runs/stop.flag` halts loop when created

### Gates
- `make verify` runs ruff+mypy+pytest; keep green
- **No command** touches `/home/*` or `~/.cache/*` (check `make doctor`)

## Runbooks

### Check CUA Setup
```bash
make check-cua
# Or directly:
uv run python -m yc_matcher.interface.cli.check_cua
```

### Headless Adapter Smoke
```bash
make browsers              # if using Playwright fallback
PLAYWRIGHT_HEADLESS=1 make test-int
```

### Headful HIL (CUA preferred)
```bash
export ENABLE_CUA=1
export YC_MATCH_URL="https://www.startupschool.org/cofounder-matching"
make run
```

### Failure Policy
- Print **first 50 lines** of the failure **verbatim**
- Apply the **smallest patch** (targeted selector or env fix)
- Re-run the failing step

## Test Matrix (maps to 02 & 03)

| ID | What | How |
|----|------|-----|
| INT-NAV-CUA-01 | CUA open listing + open first profile | `PLAYWRIGHT_HEADLESS=1 make test-int` + CUA mock |
| INT-FALLBACK-01 | Forced CUA failure → Playwright path | env flip + adapter smoke |
| INT-MSG-01 | Template render + conditional send | shadow on/off, threshold gate |
| INT-VERIFY-01 | Post-send verify + retry ≤1 | instrument DOM/visual confirm |
| INT-QUOTA-01 | Daily/weekly limits enforced | set low quotas; assert `quota_exceeded` |
| INT-STOP-01 | STOP halts within ≤2s | create `.runs/stop.flag` mid-run |
| UNIT-DEC-01 | Advisor/Rubric/Hybrid math | deterministic fixtures |
| UNIT-LOG-01 | `events.jsonl` schema | schema assertions |
| INT-LOCAL-01 | No `$HOME` writes | run under temp HOME; audit paths |

## Rollout Plan

- **Canary**: 10 profiles, collect metrics (success rate, false-positive sends, avg latency, cost)
- **Promote**: raise quotas if success rate/latency/cost OK
- **Rollback**: flip `CUA_MODEL`/`OPENAI_DECISION_MODEL` envs; retain Playwright fallback

## Tech Notes
- Primary engine: OpenAI Computer Use via Agents SDK (CUA model from env)
- Screenshot handling: Computer Use tool handles capture automatically
- Action execution: `Agent.run()` with `ComputerTool` for click, type, etc.
- Fallback: Playwright adapter only when CUA unavailable
- Env flags respected: `DECISION_MODE`, `THRESHOLD`, `ALPHA`, `STRICT_RULES`, repo-scoped caches

## Safety & Pacing
- Quotas (daily/weekly) with SQLite (`.runs/quota.sqlite`); deny when exhausted
- Dedupe (`.runs/seen.sqlite`) hashed by (profile URL + name)
- STOP toggle in UI writes `.runs/stop.flag`
- Shadow mode = **never send**, only log decisions
- Event log is append-only JSONL with versioned schema
- Pacing delays between sends (`SEND_DELAY_MS`)

## Risk & Mitigation
- **CUA access not enabled** → Mitigation: `make check-cua`; switch to `ENABLE_PLAYWRIGHT_FALLBACK=1`
- **DOM/visual drift** → Mitigation: CUA perception first; Playwright targeted selector fallbacks
- **Rate limits / ToS** → Mitigation: quotas + pacing; no credential storage; HIL login
- **Cost spikes** → Mitigation: `model_usage` events, canary before rollout, `SHADOW_MODE=1` dry-runs
- **Data leakage** → Mitigation: no full screenshot retention; minimal derived text only; JSONL redaction
- **Provider limits**: status indicator; graceful fallback; Shadow Mode
- **Site changes**: resilient find/click strategies; Playwright fallback smoke tests
- **Failures**: Log first 50 lines, apply minimal patch, retry