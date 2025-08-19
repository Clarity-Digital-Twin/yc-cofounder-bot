Scope and Requirements

## In-Scope (MVP: Autonomous Matching Agent)
- **User Profile Setup**: One-time entry of user's profile, match criteria, message template
- **Autonomous Browsing via OpenAI CUA**:
  - Open YC cofounder matching site (WEBSITE_LINK.MD)
  - Navigate profile list autonomously
  - Take screenshots, click "View profile" for each candidate
  - Extract profile text from screenshots
- **Intelligent Matching**:
  - Evaluate each candidate against user's criteria
  - Produce structured decision: {match_score, decision, rationale, compatibility_notes}
  - Apply configurable threshold for auto-send (e.g., score > 80%)
- **Automated Messaging**:
  - Fill message form with personalized template
  - Click "Invite to connect" for matches above threshold
  - Respect quota limits (daily/session caps)
- **Streamlit Dashboard**:
  - User profile editor (load from CURRENT_COFOUNDER_PROFILE.MD)
  - Match criteria configuration
  - Message template editor (load from MATCH_MESSAGE_TEMPLATE.MD)
  - Real-time event log and match decisions
  - Start/Stop controls
- **Safety & Tracking**:
  - SQLite deduplication (never message same profile twice)
  - JSONL event logging with timestamps
  - Quota enforcement (hard limits)
  - Emergency stop button (.runs/stop.flag)

## Out-of-Scope (MVP)
- Manual profile pasting (old approach - we're autonomous now)
- Complex Playwright scripting (CUA handles browser control)
- Multi-site support (focus on YC only)
- CAPTCHA solving (manual intervention if needed)
- Background scheduling (manual start for now)
- External CRM integrations

## Functional Requirements

### User Experience
- **Profile Input**: Rich text area for user's background, skills, vision
- **Criteria Builder**: Define ideal cofounder (skills, domain, location, etc.)
- **Template Editor**: Customize outreach message with placeholders
- **Live Monitoring**: See CUA's actions, decisions, and messages in real-time
- **Session Summary**: Profiles viewed, matches found, messages sent, cost

### Matching Engine
- **Compatibility Scoring**: AI evaluates candidate against user's criteria
- **Structured Output**: JSON with score, decision, rationale
- **Threshold-based Actions**: Only message high-score matches
- **Explanation**: Clear reasoning for each accept/reject decision

### CUA Browser Control
- **Screenshot-based Navigation**: CUA sees what human sees
- **Natural Actions**: Click buttons by visible text, fill forms
- **Error Recovery**: Retry failed actions with backoff
- **State Tracking**: Remember position in profile list

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

### OpenAI CUA
- **API Access**: Tier 3-5 for Responses API with computer_use tool
- **Model**: CUA or gpt-4o with computer use capability
- **Token Budget**: 4000 tokens per action, 0.3 temperature

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
- **Match Threshold**: 80% compatibility for auto-send
- **Session Quota**: 10 messages per run
- **Daily Quota**: 20 messages per day
- **Rate Limit**: 5-10 seconds between actions
- **Max Retries**: 3 attempts for failed actions

## Success Metrics
- **Automation Rate**: 90% of profiles processed without intervention
- **Match Quality**: 80% of sent messages to relevant matches
- **Cost Efficiency**: < $0.03 per profile processed
- **User Satisfaction**: Setup in < 10 minutes, results in < 30 minutes