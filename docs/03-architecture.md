Architecture

Principles
- Keep orchestration minimal; leverage OpenAI’s Computer Use with a thin Playwright adapter.
- Prefer human‑visible, supervised operation; no hidden background actions.
- Use simple local storage (SQLite/JSON) only where it adds clear value.

High‑Level Components
- Decision Engine (HIL Paste Mode): OpenAI model prompt that takes Profile Text + Criteria + Template and returns {decision, rationale, message}.
- Agent Orchestrator (Semi‑Auto): OpenAI Agents SDK + `ComputerTool` for optional auto‑send actions.
- Computer Adapter: Playwright (Chromium, headful) implementing the Computer interface (screenshot, click, type, scroll, keypress, drag, wait, move).
- Tools:
  - quota_guard(limit): increments/guards the send count (hard stop when exceeded).
  - templates: resolved message template variables (e.g., candidate name if present).
  - scoring (optional): simple rubric to support decision rationale.
- UI Layer:
  - Streamlit app (preferred) with panes for criteria, template, paste profile, results, and optional send button. CLI as fallback.
- Config & Secrets:
  - `.env` for OPENAI_API_KEY and URL; app args for run‑time overrides.
- Persistence (lightweight):
  - JSON counter for quota; optional SQLite for run/session logs, dedupe, and saved drafts.

Data Flow
HIL Paste Mode (MVP)
1) Operator enters Criteria + Template in UI.
2) Operator pastes Profile Text; presses “Evaluate”.
3) Model returns Yes/No, rationale, and a draft message.
4) Operator edits/approves; optionally clicks “Send via browser”.

Semi‑Auto Browser Mode (Next)
1) Headful browser opens Startup School cofounder-matching URL (WEBSITE_LINK.MD); operator logs in (see initial_log_in.png).
2) Agent clicks “View profile”, reads the profile, drafts message using the configured template.
3) Before sending, agent focuses the right‑panel message box; calls `quota_guard`; on approval, clicks “Send” or “Skip”.
4) Stops when quota reached or candidates exhausted.

Key Configs
- Model: `computer-use-preview` (OpenAI Responses/Agents SDK backend).
- Display: 1280×800 or similar to reduce screenshot size and keep layout stable.
- Timeouts: per‑step wait 0.5–2s; max overall runtime configurable.
- Quota: integer per run; default 5.

Security & Privacy
- No credentials in prompts.
- Local `.env`, not committed; recommend `pre-commit` to block secrets.

Extensibility
- Add a Streamlit UI by wrapping the run() coroutine and streaming logs.
- Add per‑site adapters if needed later; keep the Computer interface stable.
