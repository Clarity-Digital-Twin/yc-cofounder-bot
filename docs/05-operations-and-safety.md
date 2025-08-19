Operations & Safety

ToS & Platform Respect
- Keep batches small; avoid spammy behavior.
- Insert small human‑like delays between actions.
- Stop after N sends; never attempt to bypass rate‑limits or CAPTCHAs.

Human‑in‑the‑Loop Controls
- HIL Paste Mode: explicit approve/send buttons; easy edit before send.
- Semi‑Auto: headful browser so the operator can pause/abort anytime.
- Optional safety prompts surfaced from the Agents SDK.

Secrets & Privacy
- Use `.env` for OPENAI_API_KEY; do not log secrets.
- Do not include credentials in prompts or screenshots.

Observability
- Console logs with timestamps and levels.
- Optional: capture last screenshot on error for troubleshooting.

Cost Guardrails
- Small model prompts and short outputs.
- Max steps per run; max tokens per response.

Runbook (MVP: HIL Paste Mode)
1) Ensure `.env` has `OPENAI_API_KEY`. Start Streamlit.
2) Enter Criteria, Template, and Quota.
3) Paste a candidate profile; click Evaluate.
4) Review decision/rationale and draft; optionally Send via browser.
5) Review session summary/export.
