Implementation Plan

Milestones

M0 — Repo hygiene and configs
- Decide package name and license.
- Add base docs (this folder) and `.gitignore`.
- Confirm OpenAI access to `computer-use-preview`.

M1 — MVP HIL Paste Mode (Streamlit or CLI)
- Create modern Python project (uv + `pyproject.toml`).
- Streamlit UI with inputs: Criteria, Template, Quota.
- Paste Profile → decision (Yes/No + rationale) + draft message.
- Quota counter and per‑session log; export summary.
 - Use MATCH_MESSAGE_TEMPLATE.MD as the default template; allow edits per session.

M2 — Semi‑Auto Browser Mode
- Playwright adapter implementing the Computer interface.
- Agents SDK integration with `ComputerTool` and `quota_guard`.
- Manual login; optional “Send via browser” from UI, with approval gate.
- Screenshots on send; improved logs.
 - Actions aligned to UI: click “View profile”, populate right‑panel message box, click “Send” or “Skip”.

M3 — Targeting quality
- Add simple `score_profile` heuristic tool and `message_template` helper.
- Add per‑run dedupe (avoid repeats using session history).

M4 — Robustness & polish
- Add small delays between sends; make selectors/coordinates more resilient.
- Add error handling for common navigation dead‑ends.
- Improve observability: structured logs and optional screenshot trail.

Acceptance Criteria (M1)
- Streamlit app runs; user can set criteria/template/quota.
- Paste → returns decision + rationale + draft message in < 5s.
- Quota counter visible; exportable session summary.
 - Default URL and template preloaded from WEBSITE_LINK.MD and MATCH_MESSAGE_TEMPLATE.MD.

Risks & Mitigations
- Layout drift: keep actions general; rely on visible labels; supervised runs.
- Safety prompts: auto‑ack routine actions; escalate anything sensitive.
- Cost spikes from loops: hard cap on steps and tokens; explicit stop conditions.
