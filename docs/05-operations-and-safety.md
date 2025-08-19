Operations & Safety

ToS & Platform Respect
- Keep batches small; avoid spammy behavior.
- Insert small human‑like delays between actions.
- Stop after N sends; never attempt to bypass rate‑limits or CAPTCHAs.

Human‑in‑the‑Loop Controls
- Semi‑Auto: headful browser with explicit approve/send/skip; pause/abort anytime.
- Shadow Mode: evaluate/do not send to calibrate rubric before enabling sends (default for first 50 profiles).
- Optional safety prompts surfaced from the Agents SDK.

Secrets & Privacy
- Use `.env` for OPENAI_API_KEY; do not log secrets.
- Do not include credentials in prompts or screenshots.
 - Optional PII redaction in logs/screenshots (emails, phones, handles) via toggle.

Observability
- JSONL event log (ts,event,profile_hash,decision,chars,send_ok,tokens_in,tokens_out,cost_est,prompt_ver,rubric_ver,criteria_preset).
- Export CSV; optional last‑screenshot on error for troubleshooting.

Cost Guardrails
- Small model prompts and short outputs.
- Max steps per run; max tokens per response.
- Show estimated $/run in UI based on steps/tokens.

Pre‑flight
- Check login: assert presence of a known element; fail fast and prompt to log in.
- Verify CUA access with `make check-cua` and ensure Playwright Chromium installed.

Runbook (MVP: Semi‑Auto)
1) Ensure `.env` has `OPENAI_API_KEY`. Start Streamlit; load defaults.
2) Log in on Startup School; confirm criteria/template/quota in sidebar.
3) Enable Shadow Mode initially; review decisions and drafts, adjust rubric.
4) Toggle sending on; approve/send or skip per candidate; watch N remaining.
5) Review logs/export; confirm dedupe entries; verify stop at quota.

Failure Policy
- If “Send” verification fails twice, halt the run and surface a blocking modal; do not keep retrying.
- Respect STOP immediately; persist progress cursor to resume later.
