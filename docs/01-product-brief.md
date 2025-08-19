Product Brief

Working Name: YC Co‑Founder Matching Bot

One‑liner
- A human‑in‑the‑loop outreach agent that evaluates pasted profiles (and later automates browsing), decides whether to message based on your criteria, drafts a personalized DM using your template, and (optionally) sends it under quota and safety controls.

Why now
- OpenAI’s Computer Use model is reliable for browser tasks and integrates cleanly with Python via Playwright, enabling fast MVP delivery without site‑specific APIs.

Goals
- Mirror current workflow: paste profile → analyze → yes/no with rationale → draft message.
- Provide fields for “ideal match” criteria and a message template/tone.
- Enable optional auto‑send with strict quota and safety gates.
- Make it easy to run locally (Streamlit UI preferred) and via CLI.

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
- Modes: HIL Paste Mode (MVP), Semi‑Auto Browser Mode (next), Full Auto (later).
