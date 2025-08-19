Scope and Requirements

## In-Scope (MVP: 3-Input Autonomous System with Decision Modes)
- **3 Core Inputs**:
  1. Your Profile (Dr. Jung's background, skills, vision)
  2. Match Criteria (free text or structured fields)
  3. Message Template (personalized with variables)

- **CUA Autonomous Browsing (PRIMARY)**:
  - Open YC site → iterate profiles → read each → evaluate
  - No manual intervention required
  - Screenshot-based perception and action
  - Provider switch: CUA_PROVIDER=anthropic|openai

- **Three Decision Modes**:
  1. **Advisor**: LLM-only evaluation, HIL approval required
  2. **Rubric**: Deterministic scoring, auto-send if threshold met
  3. **Hybrid**: Combines rubric + LLM confidence, auto-send if threshold met

- **Playwright Fallback (SECONDARY)**:
  - ONLY when CUA unavailable (ENABLE_PLAYWRIGHT_FALLBACK=1)
  - Same autonomous flow, different adapter

- **Auto-Messaging with Safeguards**:
  - Send ONLY if: decision=YES + within quota + not duplicate
  - Template personalization with {name}, {tech}, {hook}, {city}, {why_match}
  - Verification of send success

- **Control & Monitoring**:
  - RUN/STOP controls
  - Mode selector (Advisor/Rubric/Hybrid)
  - Quota display (remaining daily/weekly)
  - Real-time JSONL event stream
  - Shadow Mode (evaluate-only)

## Out-of-Scope (MVP)
- Manual profile pasting (NEVER - this is the OLD broken way)
- Credential storage or automated login
- CAPTCHA breaking or automation
- Bulk spam operations
- Multi-site support (YC only initially)
- Background scheduling
- External CRM/database integrations

## Functional Requirements

### Decision Engine
- **Common Schema**: All modes output same structure
  ```json
  {
    "mode": "advisor|rubric|hybrid",
    "decision": "YES|NO",
    "rationale": "≤120 chars",
    "extracted": {...},
    "scores": {
      "rubric_score": 0.0,
      "llm_confidence": 0.0,
      "final_score": 0.0
    }
  }
  ```

- **Advisor Mode**:
  - Input: Profile text + criteria
  - Process: LLM evaluation ("Is this a good fit?")
  - Output: YES/NO + rationale
  - Sending: Manual approval required (HIL)

- **Rubric Mode**:
  - Input: Profile text + structured criteria
  - Process: Deterministic scoring (skills overlap, location match, etc.)
  - Output: YES if score ≥ threshold, NO otherwise
  - Sending: Auto-send if YES + quota available

- **Hybrid Mode**:
  - Input: Profile text + criteria
  - Process: α * llm_confidence + (1-α) * rubric_score
  - Output: YES if final_score ≥ threshold + hard rules pass
  - Sending: Auto-send if YES + quota available

### Browser Automation
- **Primary (CUA)**:
  - Anthropic Computer Use API (available now)
  - OpenAI Responses API (when available)
  - Screenshot → reasoning → action cycle

- **Fallback (Playwright)**:
  - Activated ONLY if CUA fails/unavailable
  - Selector-based automation
  - Same flow, different implementation

### Safety Features
- **Quota Management**: Daily/weekly hard limits
- **Deduplication**: SHA256 hash prevents re-messaging
- **Rate Limiting**: SEND_DELAY_MS between actions
- **Stop Control**: Immediate abort via flag
- **Audit Trail**: Complete JSONL log of all actions

## Non-Functional Requirements

### Performance
- Profile processing: < 30 seconds per profile
- Token efficiency: < 2000 tokens per evaluation
- Cost target: < $0.50 per 20-profile session
- Reliability: 95% success rate for browser actions

### Security & Privacy
- API keys stored in .env, never in code or logs
- No credential storage
- PII handling with optional redaction
- Isolated browser sessions

### Provider Configuration
```bash
ENABLE_CUA=1
CUA_PROVIDER=anthropic  # or openai
CUA_API_KEY=...
ENABLE_PLAYWRIGHT_FALLBACK=1
DECISION_MODE=advisor  # or rubric or hybrid
THRESHOLD=0.72
ALPHA=0.30  # for hybrid mode
STRICT_RULES=1
```

## Configuration Defaults
- **Decision Mode**: advisor (safest default)
- **Match Threshold**: 0.72 (for rubric/hybrid)
- **Alpha**: 0.30 (hybrid weight for LLM)
- **Daily Quota**: DAILY_LIMIT=20
- **Weekly Quota**: WEEKLY_LIMIT=60
- **Pacing**: SEND_DELAY_MS=5000
- **Provider**: CUA_PROVIDER=anthropic

## Acceptance Criteria
- **Dry Run**: Shadow Mode shows decision events without sending
- **Live Run**: Logs sent{ok:true} for each message
- **Mode Switching**: Can toggle between Advisor/Rubric/Hybrid
- **Provider Switch**: Can toggle between CUA/Playwright
- **Quota Enforcement**: Hard stop at limits
- **STOP Works**: Immediate halt when triggered
- **Decision Logging**: Every decision includes mode, scores, rationale
- **Audit Trail**: Complete JSONL with versioning (prompt_ver, rubric_ver)