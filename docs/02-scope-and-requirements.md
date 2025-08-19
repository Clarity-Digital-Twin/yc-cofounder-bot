Scope and Requirements

## In-Scope (MVP: 3-Input Autonomous System)
- **3 Core Inputs**:
  1. Your Profile (Dr. Jung's background, skills, vision)
  2. Match Criteria (what you're looking for in a cofounder)
  3. Message Template (personalized outreach)
- **CUA Autonomous Browsing (PRIMARY)**:
  - Open YC site → iterate profiles → read each → evaluate
  - No manual intervention required
  - Screenshot-based perception and action
  - Provider switch: CUA_PROVIDER=openai|anthropic
- **Playwright Fallback (SECONDARY)**:
  - ONLY when CUA unavailable (ENABLE_PLAYWRIGHT_FALLBACK=1)
  - Same autonomous flow, different adapter
- **Local Decision Engine**:
  - Evaluate against YOUR criteria (not generic)
  - Structured output: {score, YES/NO, rationale}
  - Configurable threshold (default 80%)
- **Auto-Messaging with Safeguards**:
  - Send ONLY if: match=YES + within quota + not duplicate
  - Template personalization with {name}, {tech}, {hook}
  - Verification of send success
- **Control & Monitoring**:
  - RUN/STOP controls
  - Quota display (remaining daily/weekly)
  - Real-time JSONL event stream
  - Pacing control (SEND_DELAY_MS)

## Out-of-Scope (MVP)
- Manual profile pasting (NEVER - this is the OLD broken way)
- Credential storage (user logs in manually if needed)
- CAPTCHA breaking or automation
- Bulk spam operations
- Multi-site support (YC only initially)
- Background scheduling
- External CRM/database integrations

## Functional Requirements

### User Experience
- **3 Inputs Only**:
  - Your Profile text area
  - Match Criteria checkboxes/sliders
  - Message Template with variables
- **One-Click Run**: Start autonomous session
- **Real-Time Monitoring**: See decisions and sends as they happen
- **Emergency Stop**: Immediate halt capability
- **Quota Display**: Always visible remaining sends

### Matching Engine
- **Compatibility Scoring**: AI evaluates candidate against user's criteria
- **Structured Output**: JSON with score, decision, rationale
- **Threshold-based Actions**: Only message high-score matches
- **Explanation**: Clear reasoning for each accept/reject decision

### Browser Automation
- **Primary (CUA)**:
  - OpenAI Responses API with computer-use-preview
  - Screenshot → reasoning → action cycle
  - Natural language understanding of UI
- **Fallback (Playwright)**:
  - Activated ONLY if CUA fails/unavailable
  - Selector-based automation
  - Same flow, different implementation

### Safety Features
- **Quota Management**: Hard limits per session/day/week
- **Deduplication**: SHA256 hash of profiles to prevent re-messaging
- **Rate Limiting**: Configurable delays between actions
- **Stop Control**: Immediate abort via UI button
- **Audit Trail**: Complete JSONL log of all actions

## Non-Functional Requirements

### Performance
- **Profile Processing**: < 30 seconds per profile (including evaluation)
- **Token Efficiency**: < 1000 tokens per profile evaluation
- **Cost Target**: < $0.50 per 20-profile session
- **Reliability**: 95% success rate for browser actions

### Security & Privacy
- **API Keys**: Stored in .env, never in code or logs
- **No Credential Storage**: CUA doesn't see login credentials
- **PII Handling**: Optional redaction in logs
- **Isolated Sessions**: Each run in separate browser context

### Compliance
- **Site ToS**: Respect rate limits and usage policies
- **Ethical Use**: Only for legitimate cofounder matching
- **Transparency**: Clear about automated nature when appropriate

## Technical Requirements

### Provider Configuration
- **OpenAI CUA**: Tier 3-5 Responses API access required
- **Anthropic CUA**: Computer Use API (if preferred)
- **Environment Variables**:
  - ENABLE_CUA=1
  - CUA_PROVIDER=openai|anthropic
  - CUA_API_KEY=...
  - ENABLE_PLAYWRIGHT_FALLBACK=1

### Infrastructure
- **Python**: 3.12+ with async support
- **Storage**: SQLite for persistence, JSONL for logs
- **UI**: Streamlit 1.28+ for dashboard
- **Browser**: Chromium for CUA control

## Assumptions
- User has OpenAI API key with CUA access (tier 3-5)
- YC site structure remains relatively stable
- Manual login acceptable for initial MVP
- Cost of $3/1M input tokens is acceptable

## Configuration Defaults
- **Match Threshold**: 80% for auto-send
- **Daily Quota**: DAILY_LIMIT=20
- **Weekly Quota**: WEEKLY_LIMIT=60
- **Pacing**: SEND_DELAY_MS=5000 (5 seconds)
- **Provider**: CUA_PROVIDER=openai (primary)
- **Fallback**: ENABLE_PLAYWRIGHT_FALLBACK=1

## Acceptance Criteria
- **Dry Run**: Shows decision events without sending
- **Live Run**: Logs sent{ok:true} for each message
- **Zero Manual Input**: No profile pasting required
- **Provider Switch**: Can toggle between CUA/Playwright
- **Quota Enforcement**: Hard stop at limits
- **STOP Works**: Immediate halt when triggered