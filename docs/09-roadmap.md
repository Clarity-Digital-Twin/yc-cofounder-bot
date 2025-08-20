Roadmap

M1 — Core CUA + Modes + Fallback (Week 1)
- OpenAI CUA adapter (primary) and ports in place
- Decision modes (Advisor, Rubric, Hybrid) with shared schema
- Streamlit UI (3 inputs, controls, events)
- JSONL events wired; Playwright fallback behind flag

M2 — Robustness & Safety (Week 2)
- STOP flag + state preservation; quotas + dedupe (SQLite)
- Pacing and backoff; Shadow Mode; optional HIL
- Cost tracking and token limits; provider status

M3 — OpenAI CUA Adapter (Week 3)
- OpenAI CUA adapter; provider switching via config
- Parity contract tests; docs and UI reflect provider choice

M4 — Ranking & Analytics (Week 4)
- Ranking view; decision distribution; quota burndown
- Prompt/rubric versioning surfaced; criteria hash in UI
- CSV export; basic cost analytics

Later (Evaluate Carefully)
- Multi-site adapters (only if ToS permits and needed)
- Prompt/policy management UI for collaboration
- Advanced observability (session timelines, screenshots on error)
