Scope and Requirements

In‑Scope (MVP: HIL Paste Mode)
- Streamlit (or CLI) inputs for:
  - Ideal match criteria (free‑text box, persisted per session)
  - Message template/tone (free‑text box with variables)
  - Quota limit (N) and optional pacing
- Paste a candidate profile’s text; system returns:
  - Yes/No decision with short rationale
  - Draft message (≤ 500 chars) using the template
- Optional: “Send via browser” button triggers semi‑auto flow with safety gates
- Enforce send quota via `quota_guard(limit=N)`; clear logs and summary
 - Default assets: load WEBSITE_LINK.MD for the start URL; load MATCH_MESSAGE_TEMPLATE.MD as the default outreach template.

Out‑of‑Scope (MVP)
- Automated login, CAPTCHA solving, or device verification.
- Background daemon/scheduler; runs are manual.
- External datastore integrations (CRM, Google Sheets, etc.).

Functional Requirements
- Decisioning: produce yes/no + rationale from pasted profile vs criteria.
- Messaging: render a concise personalized DM via a template (with variables like {name}, {common_interest}, {why_match}).
- Safety: before any auto‑send, call `quota_guard`; respect hard stop.
- Human‑in‑the‑loop: clear approve/send buttons; visible browser when sending.
- Observability: UI logs and per‑profile summary; optional screenshots when sending.
- Idempotence: track sent profiles within a session to avoid duplicates.
 - UI specifics (semi‑auto): support clicking “View profile”, using the right‑side message box, and “Send”/“Skip”.

Non‑Functional Requirements
- Reliability: resilient to minor UI changes; supervised.
- Compliance: respect site ToS; rate‑limit and keep batch small.
- Security: keep secrets local; the model never sees credentials.
- Cost: token use bounded by small batch runs and short prompts.
- Portability: runs on macOS/Windows/Linux with Chromium.

Assumptions
- Operator holds an OpenAI API key with access to the Computer Use preview model.
- Manual login is acceptable; session persists for the run.
- The site’s UI is largely navigable via vision (screenshots) and clicks.
- For MVP, user can paste profile text; browser automation is optional.

Open Questions (to confirm)
- Exact target URL (Startup School vs YC portal) to begin from.
- Preferred tone/style and any messaging constraints; initial template example.
- Criteria defaults (skills, seniority, location, availability, deal‑breakers).
- Daily/weekly quota and pacing between messages.
- Whether to store lightweight history (SQLite) to avoid repeat outreach across runs.
