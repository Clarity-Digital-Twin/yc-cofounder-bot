Implementation Plan

Milestones

M0 — Repo hygiene and configs
- Decide package name and license.
- Add base docs (this folder) and `.gitignore`.
- Confirm OpenAI access to `computer-use-preview`.

M1 — MVP Semi‑Auto (headful, HIL approvals)
- Streamlit UI: criteria, template, quota, N remaining, approve/send/skip.
- Agents SDK + Playwright: navigate list, click “View profile”, focus right panel.
- Decisioning: schema‑validated outputs; deterministic rubric gate; rationale/draft from model.
- Safety: quota_guard, STOP switch, per‑run max steps/tokens.
- Observability: JSONL event log; SQLite dedupe; export summary.
- Defaults: preload URL from WEBSITE_LINK.MD; template from MATCH_MESSAGE_TEMPLATE.MD.

M2 — Quality upgrades (P1–P5)
- P1: Pydantic schema + strict parsing; weighted rubric + threshold.
- P2: SQLite seen‑profiles + JSONL log + prompt versioning.
- P3: click_by_text helpers + retry/jitter wrappers; screenshot on send.
- P4: UI polish: side‑by‑side review; Approve & Copy; N remaining; Export CSV.
- P5: Shadow Mode to calibrate rubric (no sends; collect human labels).

M3 — Targeting quality
- Improve scoring weights; add criteria presets; A/B template variants.

M4 — Robustness & polish
- Advanced observability (session viewer); better error handling for dead‑ends; cost estimates in UI.

Acceptance Criteria (M1)
- Headful browser navigates to profiles; “View profile” and message box interactions work.
- For each candidate, show decision (schema‑validated) + rationale + draft; on approval, quota_guard enforced; click Send; stops exactly at N.
- JSONL logs and SQLite dedupe in place; default URL/template preloaded.

Risks & Mitigations
- Layout drift: keep actions general; rely on visible labels; supervised runs.
- Safety prompts: auto‑ack routine actions; escalate anything sensitive.
- Cost spikes from loops: hard cap on steps and tokens; explicit stop conditions.
