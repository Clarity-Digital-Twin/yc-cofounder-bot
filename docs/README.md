YC Co-Founder Autonomous Matching Agent — Documentation

## Purpose
An autonomous matching agent that uses a Computer Use Agent (CUA) to browse YC cofounder profiles, evaluate compatibility against YOUR criteria, and (when approved) send connection invites — all from a single Streamlit dashboard with safety controls.

## Key Concept
- **3 inputs**: Your Profile, Match Criteria, Message Template
- **CUA primary**: OpenAI CUA via Responses API
- **Playwright fallback**: Only when CUA is unavailable
- **Decision modes**: Advisor (LLM-only), Rubric (deterministic), Hybrid (combined)
- **Safety**: STOP flag, quotas, pacing, dedupe, JSONL audit

## Documentation Map
- `01-product-brief.md` — 3-input system, CUA primary, modes
- `02-scope-and-requirements.md` — In-scope/out-of-scope, functional/non-functional reqs
- `03-architecture.md` — Ports/adapters, decision schema, events
- `04-implementation-plan.md` — Milestones M1–M4 (CUA+modes, robustness, OpenAI adapter, analytics)
- `05-operations-and-safety.md` — STOP, quotas, HIL, platform respect
- `06-dev-environment.md` — Env flags, setup, Make targets, repo-scoped caches
- `07-project-structure.md` — DDD layout, ports, adapters
- `08-testing-quality.md` — TDD plan, gates, contract tests
- `09-roadmap.md` — Milestones and later options
- `10-ui-reference.md` — Single-page UI with mode selector and live events
- `11-engineering-guidelines.md` — Clean code, ports, DI, logging
- `12-prompts-and-rubric.md` — Prompts, scoring, hard rules, versioning

## Quick Start
1. Create `.env` from `.env.example` and set `CUA_API_KEY`.
2. Choose mode: `DECISION_MODE=advisor` (default).
3. Start UI: `make run` (or `streamlit run src/app/interface/web/ui_streamlit.py`).
4. Fill 3 inputs. Select mode. Optionally enable Shadow Mode.
5. Click RUN. Monitor events. Use STOP anytime. Approve sends in Advisor mode.

## Events & Safety
- Emits JSONL: `decision`, `sent`, `stopped`, `model_usage` (with `prompt_ver`, `rubric_ver`, `criteria_hash`).
- Enforces hard limits: `DAILY_LIMIT`, `WEEKLY_LIMIT`, `SEND_DELAY_MS`.
- Dedupes by profile hash; verifies send success before logging `sent{ok:true,mode}`.

## Stack
- **Automation**: OpenAI CUA (primary), Playwright fallback
- **UI**: Streamlit
- **Storage**: SQLite (quota/dedupe), JSONL logs
- **Lang**: Python 3.12+

## Architecture Shift
- Old: paste candidate profiles manually; Playwright as primary
- New: single control panel with 3 inputs; CUA browses autonomously; backend evaluates per mode; CUA sends when approved

## Costs & Performance Targets
- Decision: < 5s; message: < 3s; total/profile: < 30s
- Tokens: decision < 2000; message < 1000
- Session cost goal: <$0.50 per ~20 profiles

See `04-implementation-plan.md` for milestones and `06-dev-environment.md` for configuration.
