# 09 — Roadmap

**Status:** Draft v0.2 (2025-08-20)  
**Owner:** Product / Eng  
**Related:** [02-scope-and-requirements.md] · [03-architecture.md] · [04-implementation-plan.md]

**Product North Star:** One-click, **hands-off matcher**. You paste **(1) Your Profile**, **(2) Match Criteria**, **(3) Message Template** — the system **autonomously** browses YC Cofounder Matching via **OpenAI Computer Use (CUA, Agents SDK)**, evaluates profiles, and **sends** messages when appropriate. **Playwright** runs only as a **fallback**.

**Traceability:** Roadmap gates map to requirements in **02 — Scope & Requirements** (FR-xx, NFR-xx, AC-xx) and design in **03 — Architecture**.

---

## Milestones & Gates

> Each milestone **must** satisfy its **Exit Criteria** (tests + AC). If a gate fails, revert or fix before proceeding.

### M0 — Baseline Hardening (Done/Keep Green)
**Goal:** Repo-scoped execution; quality gates.

**Work:**
- Makefile exports repo-local caches only; no writes to `$HOME` (NFR-06)
- `make verify` (ruff, mypy, unit tests) clean; add "doctor" output to CI logs

**Exit Criteria:**
- `make doctor` shows `UV_CACHE_DIR=.uv_cache`, `XDG_CACHE_HOME=.cache`, `PLAYWRIGHT_BROWSERS_PATH=.ms-playwright`
- `make verify` green; unit tests stable
- FR/NFR coverage references wired in test names

### M1 — CUA Foundation (PRIMARY Path) — Week 1
**Goal:** **OpenAI Computer Use** is the default browser engine.

**Work:**
- Adapter: `OpenAICUABrowser` using **Agents SDK**
  - **Package:** `openai-agents`
  - **Import:** `from agents import Agent, ComputerTool, Session`
- Env/config: `ENABLE_CUA=1`, `CUA_MODEL=<your-computer-use-model>`, `OPENAI_API_KEY`
- CLI probe: `make check-cua` (lists models, initializes agent)
- Contract tests for `ComputerUsePort`

**Exit Criteria (Gates):**
- **INT-NAV-CUA-01** (FR-01/02): Agent opens listing + iterates n≥3 profiles (mock/safe page)
- **UNIT-LOG-01** (FR-18/19/20): `events.jsonl` schema validated
- **AC-05** (fallback readiness is wired but not exercised): CUA init failure path detectable

### M2 — Decision Engine (Advisor/Rubric/Hybrid) + Template — Week 2
**Goal:** Deterministic scoring + LLM recommendation + weighted hybrid; compile message drafts.

**Work:**
- **Advisor** (LLM-only) using `OPENAI_DECISION_MODEL`
- **Rubric** (deterministic) with must-have/should-have rules
- **Hybrid**: `final = α*advisor + (1-α)*rubric` (`ALPHA` env)
- Template rendering with placeholders `{first_name}`, `{why_match}`, `{my_context}`, `{their_highlight}`, `{cta}`

**Exit Criteria (Gates):**
- **UNIT-DEC-01** (FR-06/07/08): Mode math and edge cases verified
- **UNIT-THRESH-01** (FR-09): Threshold gating correct
- **INT-EXTRACT-01** (FR-04/05): Normalize minimal profile schema from on-screen text
- **AC-01/AC-02** dry-run path produces decisions without sends

### M3 — Messaging Pipeline + Safety (STOP, Quotas, Dedupe) — Week 3
**Goal:** Safe, idempotent sending under quotas with full audit trail.

**Work:**
- Seen db (`.runs/seen.sqlite`) and quota db (`.runs/quota.sqlite`)
- STOP flag (`.runs/stop.flag`) respected before any action
- Pacing (`SEND_DELAY_MS`) between sends
- Verify-send logic with ≤1 retry (FR-13)

**Exit Criteria (Gates):**
- **INT-MSG-01** (FR-11/12): Draft → focus → fill → conditional send
- **INT-VERIFY-01** (FR-13): Post-send visual/DOM confirmation detection
- **INT-QUOTA-01** (FR-15) and **INT-STOP-01** (FR-14): hard stops honored
- **AC-03/AC-07**: quota blocks and dedupe guaranteed

### M4 — Streamlit Control Panel (3-Input UI) + Live Log — Week 4
**Goal:** The user only provides the **3 inputs** and presses **Run**.

**Work:**
- Inputs: **Your Profile**, **Match Criteria**, **Message Template** (markdown editors)
- Controls: **Run/Stop**, **Decision Mode**, `THRESHOLD`, `ALPHA`, **Shadow Mode**
- Status: CUA connectivity, fallback indicator, quota counters, last action
- Tail of `events.jsonl` + download button

**Exit Criteria (Gates):**
- **AC-01**: Single run processes ≥10 profiles; logs every action
- **AC-06**: `{"event":"sent","ok":true,"mode":"auto","verified":true}` present for successes
- **NFR-07**: Observability complete

### M5 — Fallback & Resilience (Playwright Path) — Week 5
**Goal:** Same flow via Playwright when CUA is unavailable or fails mid-run.

**Work:**
- `ENABLE_PLAYWRIGHT_FALLBACK=1` wiring; same `BrowserPort` contract
- Targeted YC selectors (role=button/link, exact/non-exact text) with minimal hard-coded fallbacks

**Exit Criteria (Gates):**
- **INT-FALLBACK-01** (FR-17): Forced CUA failure triggers Playwright path through send/verify
- **NFR-02**: Minor layout/text variation does not break flow

### M6 — Production Hardening & Canary — Week 6
**Goal:** Reliability, cost, and rollbacks.

**Work:**
- Cost usage logging (`model_usage` events)
- Canary subset with manual audit; compare success rate, latency, token cost
- Model upgrades via **env only** (`CUA_MODEL`, `OPENAI_DECISION_MODEL`) per `MODEL_SELECTION.md`

**Exit Criteria (Gates):**
- Canary ≥95% action reliability; ≤3% false-positive sends (NFR-03)
- Rollback documented and tested

---

## Work Items (Backlog, Linked to FR/NFR/AC)

- **R-01** FR-01/02: `OpenAICUABrowser.open/listing_iterate` (INT-NAV-CUA-01)
- **R-02** FR-04/05: On-screen text extraction → `CandidateProfile`
- **R-03** FR-06: Advisor decision (`OPENAI_DECISION_MODEL`)
- **R-04** FR-07: Rubric rules (must/should)
- **R-05** FR-08/09: Hybrid scoring + threshold
- **R-06** FR-11/12: Template render + conditional send
- **R-07** FR-13: Verify-send + retry≤1
- **R-08** FR-14/15: STOP + quota + pacing
- **R-09** FR-16: Shadow mode (evaluate-only)
- **R-10** FR-17: Playwright fallback wiring
- **R-11** FR-18/19/20: `events.jsonl`, seen/quota persistence
- **R-12** NFR-06/07: Repo-scoped caches; observability polish
- **R-13** AC-01..07: Acceptance test harness
- **R-14** UI-Inputs: 3 markdown editors + validation
- **R-15** UI-Controls: Mode/Threshold/Alpha/Run/Stop/Shadow
- **R-16** UI-Status: CUA/fallback/quota/last action
- **R-17** Model selection doc finalization (`MODEL_SELECTION.md`)
- **R-18** Cost/usage logging (`model_usage` event)
- **R-19** Canary & rollback runbook
- **R-20** YC targeted selector fallbacks (Playwright only)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Site anti-bot / UI drift | High | Use CUA vision for robustness; keep Playwright fallbacks ultra-targeted |
| Access tier to CUA models | High | Verify via `make check-cua`; block UI with clear status if unavailable |
| Model churn/cost variance | Medium | Env-driven model names; canary before switch |
| Rate limits / quotas | Medium | Enforce daily/weekly quotas and pacing; STOP always wins |
| WSL/permissions & browser download | Low | Repo-local caches; document offline Playwright cache if needed |
| Ethics/ToS | High | Human-like pacing, no bulk scraping/export; ephemeral per-profile processing only |

---

## Configuration (Single Source of Truth)

```env
# Engines
ENABLE_CUA=1
ENABLE_PLAYWRIGHT_FALLBACK=1
ENABLE_PLAYWRIGHT=0

# OpenAI
OPENAI_API_KEY=sk-...
CUA_MODEL=<your-computer-use-model>          # from Models endpoint
CUA_TEMPERATURE=0.3
CUA_MAX_TOKENS=1200
OPENAI_DECISION_MODEL=<your-best-llm>        # Advisor/Hybrid

# Decision
DECISION_MODE=hybrid                         # advisor|rubric|hybrid
THRESHOLD=0.72
ALPHA=0.50

# Runtime
YC_MATCH_URL=https://www.startupschool.org/cofounder-matching
SEND_DELAY_MS=5000
DAILY_QUOTA=25
WEEKLY_QUOTA=120
SHADOW_MODE=0                                # 1 = evaluate-only

# Local paths (no $HOME writes)
UV_CACHE_DIR=.uv_cache
XDG_CACHE_HOME=.cache
PLAYWRIGHT_BROWSERS_PATH=.ms-playwright
MPLCONFIGDIR=.mplconfig
```

---

## Future Enhancements (Post-MVP)

### Near-term (Evaluate Carefully)
- Enhanced analytics dashboard with success metrics
- Batch scheduling for off-peak processing
- Advanced template variables and conditional logic
- Profile similarity scoring for better matches

### Long-term (If Validated)
- Multi-platform support (AngelList, etc.) - **only if ToS permits**
- ML-based profile ranking and recommendation
- Collaborative filtering based on successful matches
- API endpoints for programmatic access

---

## Definition of Done (Roadmap)

- All milestones pass their **Exit Criteria** and related **AC**
- "CUA-first" is the default path; Playwright only when enabled as fallback
- UI exposes exactly **3 inputs** + controls; logs and DBs reflect reality
- No `$HOME` writes; all artifacts under repo; logs are tail-viewable and downloadable
- Each milestone has test coverage and passes `make verify`