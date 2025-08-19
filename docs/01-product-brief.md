Product Brief

Working Name: YC Co‑Founder Matching Bot

One‑liner
- A semi‑autonomous outreach agent for YC/Startup School cofounder matching that navigates profiles, evaluates fit using a transparent rubric, drafts a templated DM, and (with HIL approval) sends under strict quotas and safety controls.

Why now
- OpenAI’s Computer Use model is reliable for browser tasks and integrates cleanly with Python via Playwright, enabling fast MVP delivery without site‑specific APIs.

Goals
- Autonomous browsing with human‑in‑the‑loop approvals at key gates (send/skip).
- High‑quality decisions: structured outputs (schema) + transparent scoring rubric.
- Draft messages that strictly follow your template and safety rules.
- Quota enforcement, cross‑run dedupe, and observable runs (JSONL + summary).
- Streamlit UI for control and review; CLI for power users.

Non‑Goals (for MVP)
- Full automation of credential entry or CAPTCHA solving.
- Multisite outreach or CRM workflows.
- Advanced ML ranking beyond simple heuristic scoring.

Success Metrics (MVP)
- Setup time under 20 minutes on a clean machine.
- Paste‑and‑evaluate loop: clear yes/no with rationale in < 5s per profile.
- Messages sent match quota exactly; zero accidental over‑send.
- Subjective quality: 80%+ of messages acceptable on first draft.

Stakeholders & Usage
- Primary user: founder/operator initiating curated outreach sessions.
- Operation cadence: small batches (e.g., 3–10 messages) with human supervision.
- Modes: Semi‑Auto Browser Mode (MVP), HIL Paste Mode (diagnostics), Full Auto (later).
