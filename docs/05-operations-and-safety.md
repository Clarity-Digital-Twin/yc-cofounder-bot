# 05 — Operations & Safety

**Status:** Draft v0.2 (2025-08-20)  
**Owner:** YC Matcher Team  
**Related:** [02-scope-and-requirements.md] · [04-implementation-plan.md] · [10-ui-reference.md]

Primary automation uses **OpenAI Computer Use (CUA) via the Responses API (computer_use tool)** with **Playwright** executing actions locally. A Playwright-only adapter is used as a fallback when CUA is unavailable or explicitly disabled.

## Operational Invariants

- **No writes to $HOME**. All caches/logs live under repo:
  - `UV_CACHE_DIR=.uv_cache`
  - `XDG_CACHE_HOME=.cache`
  - `PLAYWRIGHT_BROWSERS_PATH=.ms-playwright`
  - `MPLCONFIGDIR=.mplconfig`
- **State files (repo-local)**:
  - Audit log: `events.jsonl` (append-only newline JSON)
  - Dedupe DB: `.runs/seen.sqlite`
  - Quota DB: `.runs/quota.sqlite`
  - Kill switch: `.runs/stop.flag`

## Configuration (Ops)

```bash
# Core
OPENAI_API_KEY=sk-...
ENABLE_CUA=1
CUA_MODEL=<your-computer-use-model>   # from Models endpoint
ENABLE_PLAYWRIGHT_FALLBACK=1          # use Playwright only if CUA fails/unavailable

# Decision Engine
DECISION_MODE=advisor|rubric|hybrid
OPENAI_DECISION_MODEL=<your-best-llm> # for Advisor/Hybrid prompts
THRESHOLD=0.72
ALPHA=0.50

# Safety & Pacing
DAILY_QUOTA=25
WEEKLY_QUOTA=120
PACE_MIN_SECONDS=45                   # minimum seconds between sends
SHADOW_MODE=0                         # 1 = evaluate-only, never send
YC_MATCH_URL=https://www.startupschool.org/cofounder-matching
```

## Safety Mechanisms

### STOP Control
- **Implementation**: Check `.runs/stop.flag` before navigation AND before sending
- **Response Time**: < 1 second from flag creation to halt
- **Logging**: Emits `{"event": "stopped", "reason": "user_requested"}`
- **State Preservation**: Saves progress for resume capability

### Quota Management
- **Daily Limit**: Hard stop at DAILY_QUOTA (default 25)
- **Weekly Limit**: Hard stop at WEEKLY_QUOTA (default 120)
- **Display**: Always visible in UI: "16/25 remaining today"
- **Enforcement**: Checked BEFORE each send attempt
- **Reset**: Daily at midnight UTC, weekly on Sunday
- **Storage**: `.runs/quota.sqlite`

### Pacing and Rate Limiting
- **Send Delay**: PACE_MIN_SECONDS minimum between successful sends (default 45s)
- **Action Delay**: 500-2000ms between CUA actions (human-like)
- **Profile Processing**: Minimum 10s per profile (no rushing)
- **Error Backoff**: Exponential backoff on failures (1s, 2s, 4s, 8s)

### Deduplication
- **Method**: SHA256 hash of (profile URL + name)
- **Storage**: `.runs/seen.sqlite` with (hash, timestamp, sent_flag)
- **Check**: Before evaluation to save costs
- **Scope**: Permanent (never re-message)

## Decision Mode Safety

### Advisor Mode (Safest)
- **No Auto-Send**: All messages require HIL approval
- **Queue System**: YES decisions queue for review
- **Timeout**: Approvals expire after 24 hours
- **Audit**: Both decision and approval logged

### Rubric Mode
- **Threshold Gate**: Only sends if score ≥ THRESHOLD
- **Hard Rules**: If STRICT_RULES=1, all must pass
- **Dry Run**: Test with Shadow Mode first

### Hybrid Mode
- **Dual Validation**: Combined scoring via α weighting
- **Weighted Safety**: Lower alpha = more conservative (more rubric weight)
- **Red Flag Override**: Any hard rule failure blocks send

## Shadow Mode
- **Purpose**: Evaluate without sending (calibration)
- **Activation**: Toggle in UI or SHADOW_MODE=1
- **Behavior**: Full evaluation, logs decisions, NO sends
- **Use Cases**:
  - Testing new criteria
  - Calibrating thresholds
  - Training rubric weights
  - Cost estimation

## Standard Runbooks

### SR-1: Normal Run (repo-scoped)
1) From repo root:
   ```bash
   mkdir -p .uv_cache .cache .ms-playwright .mplconfig .runs
   make doctor
   make verify
   ```
   Expect `make doctor` to print only repo-local paths (no `$HOME`), and `make verify` green.

2) Optional headless smoke (no network pages):
   ```bash
   PLAYWRIGHT_HEADLESS=1 make test-int
   ```

3) Headful HIL run:
   ```bash
   export ENABLE_CUA=1
   uv run streamlit run -m yc_matcher.interface.web.ui_streamlit --server.port 8502
   ```

4) In the browser: manually log in to YC, paste **Your Profile**, **Match Criteria**, **Message Template**, choose Decision Mode, click **Run** (or **Analyze** → **Approve & Send** in Advisor mode).

### SR-2: Immediate STOP
- **UI**: Toggle **STOP** button
- **CLI**: `touch .runs/stop.flag` (create) → system halts before any new action
- **Clear**: `rm -f .runs/stop.flag`

### SR-3: Quota Reached
- **Symptom**: No sends; logs show `{"event":"quota","allowed":false}`
- **Action**: Adjust `DAILY_QUOTA` / `WEEKLY_QUOTA`, or wait for window reset
- **Check**: `sqlite3 .runs/quota.sqlite "SELECT * FROM quotas;"`

### SR-4: Login Required
- **Symptom**: CUA reports auth wall / Playwright fails to click message box
- **Action**: Perform manual login in the visible window; resume
- **Note**: Credentials are **never** stored by the app

### SR-5: CUA Unavailable → Fallback
- **Symptom**: CUA init/action error
- **Action**: Ensure `ENABLE_PLAYWRIGHT_FALLBACK=1`; re-run
- **Behavior**: Adapter swaps to Playwright automatically

### SR-6: Selector Drift on YC (Playwright path)
- **Symptom**: Button not found (e.g., "View profile", "Send")
- **Action**: Add a **targeted fallback** text/role selector for the specific label observed
- **Location**: Update selectors in `infrastructure/playwright_browser.py`

## Privacy & Data Retention

- **No screenshots persisted**: Only derived minimal text required for decision
- **PII minimization**: Redact/shorten raw excerpts in `events.jsonl`
- **Retention**: Rotate `events.jsonl` weekly; vacuum SQLite monthly
- **No credential storage**: All authentication is manual HIL
- **ToS compliance**: Human-like pacing; no CAPTCHA breaking or bulk scraping/export

## Observability

### Event Schema
`events.jsonl`: every step logged. Canonical sent event (after verify):
```json
{"event":"sent","ok":true,"mode":"auto","verified":true,"chars":312}
```

Additional events:
- `start`: `{"event":"start","run_id":"...","mode":"hybrid","shadow":false}`
- `profile_read`: `{"event":"profile_read","url":"...","excerpt_len":1234}`
- `decision`: `{"event":"decision","mode":"hybrid","decision":"YES","scores":{...}}`
- `model_usage`: `{"event":"model_usage","provider":"openai","model":"...","tokens_in":1500,"tokens_out":200,"cost_est":0.0051}`
- `quota`: `{"event":"quota","day_count":5,"week_count":15,"allowed":true}`
- `stop`: `{"event":"stopped","reason":"user_requested"}`
- `error`: `{"event":"error","where":"send","message":"...","retryable":true}`

### Monitoring Dashboard
Real-time metrics displayed:
- Profiles/hour rate
- Success/failure ratio
- Cost accumulator
- Quota burndown (daily/weekly)
- Decision distribution
- Average scores by mode
- Last action timestamp

## Pre-Flight Checks

```bash
# 1. Verify CUA access
make check-cua

# 2. Install browsers (if using Playwright fallback)
make browsers

# 3. Run integration tests
PLAYWRIGHT_HEADLESS=1 make test-int

# 4. Dry run (Shadow Mode)
SHADOW_MODE=1 make run
```

## Readiness & Acceptance Checks

- `make doctor` shows repo-local caches only (no `/home/*`, no `~/.cache/*`)
- `make verify` green (ruff=0, mypy=0, unit tests pass)
- `PLAYWRIGHT_HEADLESS=1 make test-int` passes (adapter validated)
- Optional HIL smoke: `ENABLE_CUA=1` run; verify:
  - `events.jsonl` contains expected events
  - `.runs/seen.sqlite` updates after profile reads
  - `.runs/quota.sqlite` tracks usage
  - `.runs/stop.flag` halts when created

## Operational Best Practices

### First Run
1. Configure .env with API keys
2. Fill 3 inputs in Streamlit
3. Select Advisor mode (safest)
4. Enable Shadow Mode
5. Run 5-10 profiles
6. Review decisions and adjust

### Production Run
1. Verify quotas reset
2. Check YC login active
3. Select appropriate mode
4. Disable Shadow Mode
5. Monitor event stream
6. Use STOP if needed

### Error Recovery
- **CUA Failure**: Auto-fallback to Playwright
- **API Error**: Exponential backoff and retry
- **Send Failure**: Log, mark as failed, continue
- **Critical Error**: Stop, preserve state, alert user

## Failure Policies
- **Max Retries**: 3 attempts per action
- **Error Threshold**: Stop after 5 consecutive errors
- **Verification Required**: Must verify send success
- **State Preservation**: Always save progress
- **No Silent Failures**: All errors logged and surfaced

## Cost Controls
- **Token Limits**: Max 2000 per decision, 1000 per message
- **Model Selection**: Use appropriate models for each task
- **Caching**: Cache extracted fields for 1 hour
- **Early Exit**: Skip obviously unmatched profiles
- **Cost Display**: Real-time estimate in UI
