Implementation Plan

This plan maps directly to the SSOT: CUA primary, Playwright fallback, three decision modes, STOP/quotas/dedupe, single-page UI.

## Milestones (M1–M4)

### M1 — Core CUA + Modes + Fallback (Week 1)
- [ ] Define ports (contracts): `ComputerUsePort`, `DecisionPort`, `QuotaPort`, `SeenRepo`, `LoggerPort`, `StopController`.
- [ ] Implement OpenAI CUA adapter using Agents SDK with Computer Use tool.
- [ ] Add screenshot capture/encoding (base64 PNG, 1280x800).
- [ ] Implement computer_calls execution (click, type, scroll).
- [ ] Wire Playwright adapter (fallback) behind feature flag (`ENABLE_PLAYWRIGHT_FALLBACK=1`).
- [ ] Implement decision modes: Advisor, Rubric, Hybrid (shared `DecisionResult` schema).
- [ ] Streamlit single-page UI: 3 inputs, mode selector, threshold/alpha, strict-rules toggle, provider selector, RUN/STOP, quotas, live events.
- [ ] Emit JSONL events: `decision`, `sent`, `stopped`, `model_usage`.

### M2 — Robustness & Safety (Week 2)
- [ ] STOP flag checks before navigation and before send; state preservation.
- [ ] Quotas (SQLite): daily/weekly caps; decrement on verified `sent`.
- [ ] Deduplication (SQLite): profile hash check pre-evaluation.
- [ ] Pacing (`SEND_DELAY_MS`) and exponential backoff.
- [ ] Shadow Mode (evaluate-only) and optional HIL (`HIL_REQUIRED=1`).
- [ ] Cost tracking and token caps; provider status indicator.

### M3 — CUA Enhancement & Testing (Week 3)
- [ ] Add session management and context tracking.
- [ ] Implement retry logic with exponential backoff.
- [ ] Add token optimization (screenshot compression, context truncation).
- [ ] Full integration testing with YC site.
- [ ] Contract tests for all CUA methods.

### M4 — Ranking, Analytics, and UX Polish (Week 4)
- [ ] Ranking view and decision distribution charts.
- [ ] Prompt/rubric versioning surfaced in UI; criteria hash.
- [ ] Export CSV and simple analytics (cost, profiles/hour, success/failure).

## Deliverables by Milestone

### M1 Artifacts
- Ports and DTOs defined; adapters stubbed.
- Decision engine for Advisor/Rubric/Hybrid with shared schema.
- Streamlit page with 3 inputs and controls; events tail.
- JSONL logger writing `decision`/`sent`/`stopped`/`model_usage`.

### M2 Artifacts
- SQLite quota and dedupe repos; STOP handling and state save.
- Pacing/backoff implemented; Shadow Mode and HIL flows.
- Safety docs updated; make targets: `check-cua`, `test-browser`, `validate-config`.

### M3 Artifacts
- OpenAI adapter implemented and configurable; parity tests.
- Provider dropdown and status in UI.

### M4 Artifacts
- Analytics widgets; CSV export; versioning surfaced.

## Testing Strategy (per SSOT)
- Unit: decision math (advisor, rubric, hybrid), hard rules, template rendering, STOP, quotas, pacing, dedupe.
- Contract: `ComputerUsePort` with fakes; assert call sequences; no real browsing.
- Integration (opt-in): local HTML replayer page; Playwright fallback smoke.
- Gates: `make verify` runs ruff+mypy+pytest; keep green.

## Tech Notes
- Primary engine: OpenAI Computer Use via Agents SDK (CUA model from env).
- Screenshot handling: Computer Use tool handles capture automatically.
- Action execution: Agent.run() with ComputerTool for click, type, etc.
- Fallback: Playwright adapter only when CUA unavailable.
- Env flags respected: `DECISION_MODE`, `THRESHOLD`, `ALPHA`, `STRICT_RULES`, repo-scoped caches.

## Acceptance (M1)
- Advisor/Rubric/Hybrid modes selectable; decisions logged with versions and criteria hash.
- Verified `sent{ok:true,mode}` after successful send; quotas decrement.
- STOP, quotas, and dedupe block sends as specified.

## Risk & Mitigation
- Provider limits: status indicator; graceful fallback; Shadow Mode.
- Site changes: resilient find/click strategies; Playwright fallback smoke tests.
- Cost: token caps, early exit, caching extracted fields for 1h.
