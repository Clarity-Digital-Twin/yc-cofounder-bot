Operations and Safety

## Safety Mechanisms

### STOP Control
- **Implementation**: Check `.runs/stop.flag` before navigation AND before sending
- **Response Time**: < 1 second from flag creation to halt
- **Logging**: Emits `{"event": "stopped", "reason": "user_requested"}`
- **State Preservation**: Saves progress for resume capability

### Quota Management
- **Daily Limit**: Hard stop at DAILY_LIMIT (default 20)
- **Weekly Limit**: Hard stop at WEEKLY_LIMIT (default 60)
- **Display**: Always visible in UI: "16/20 remaining today"
- **Enforcement**: Checked BEFORE each send attempt
- **Reset**: Daily at midnight UTC, weekly on Sunday

### Pacing and Rate Limiting
- **Send Delay**: SEND_DELAY_MS between successful sends (default 5000ms)
- **Action Delay**: 500-2000ms between CUA actions (human-like)
- **Profile Processing**: Minimum 10s per profile (no rushing)
- **Error Backoff**: Exponential backoff on failures (1s, 2s, 4s, 8s)

### Deduplication
- **Method**: SHA256 hash of normalized profile ID
- **Storage**: SQLite with (hash, timestamp, sent_flag)
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
- **Dual Validation**: Both rubric and AI must agree
- **Weighted Safety**: Lower alpha = more conservative
- **Red Flag Override**: Any red flag blocks send

## Shadow Mode
- **Purpose**: Evaluate without sending (calibration)
- **Activation**: Toggle in UI or SHADOW_MODE=1
- **Behavior**: Full evaluation, logs decisions, NO sends
- **Use Cases**:
  - Testing new criteria
  - Calibrating thresholds
  - Training rubric weights
  - Cost estimation

## Human-in-the-Loop (HIL)
- **Advisor Mode**: Always requires approval
- **Optional for Others**: HIL_REQUIRED=1 forces approval
- **Approval UI**: Shows profile summary, decision, draft message
- **Actions**: Approve & Send | Edit & Send | Skip | Block

## Platform Respect
- **ToS Compliance**: Respect rate limits and usage policies
- **CAPTCHA Policy**: Stop and alert user (no bypass attempts)
- **Login**: Manual only (no credential automation)
- **Batch Size**: Small batches (10-20 per session)
- **Hours**: Avoid peak times when possible

## Privacy and Security
- **API Keys**: Only in .env, never in code/logs
- **No Credential Storage**: User logs in manually
- **Screenshot Handling**: Auto-delete after processing
- **PII Redaction**: Optional mode to redact emails/phones
- **Isolated Sessions**: Each run in new browser context

## Event Logging
Every action produces JSONL events:

```json
{"event": "start", "mode": "hybrid", "shadow": false, "quotas": {"daily": 20, "weekly": 60}}
{"event": "decision", "profile_id": "abc", "mode": "hybrid", "decision": "YES", "scores": {...}}
{"event": "sent", "profile_id": "abc", "ok": true, "mode": "auto", "verified": true}
{"event": "quota_check", "daily_remaining": 15, "weekly_remaining": 45}
{"event": "stopped", "reason": "quota_exceeded"}
{"event": "model_usage", "tokens_in": 1500, "tokens_out": 200, "cost_est": 0.0051}
```

## Cost Controls
- **Token Limits**: Max 2000 per decision, 1000 per message
- **Model Selection**: Use smaller models when possible
- **Caching**: Cache extracted fields for 1 hour
- **Early Exit**: Skip obviously unmatched profiles
- **Cost Display**: Real-time estimate in UI

## Pre-Flight Checks
```bash
# 1. Verify CUA access
make check-cua

# 2. Test browser automation
make test-browser

# 3. Validate configuration
make validate-config

# 4. Dry run (Shadow Mode)
SHADOW_MODE=1 make run
```

## Operational Runbook

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

## Monitoring Dashboard
Real-time metrics displayed:
- Profiles/hour rate
- Success/failure ratio
- Cost accumulator
- Quota burndown
- Decision distribution
- Average scores by mode