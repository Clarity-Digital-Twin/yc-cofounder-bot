Implementation Plan

## Phase 1: CUA Integration & Core Matching (Week 1)

### 1.1 OpenAI CUA Setup
- [ ] Install OpenAI SDK with Responses API support
- [ ] Create CUAAdapter implementing BrowserPort interface
- [ ] Test CUA with simple browser navigation tasks
- [ ] Implement screenshot capture and action generation

### 1.2 Matching Engine
- [ ] Create UserProfile and MatchCriteria domain entities
- [ ] Implement MatchingService for profile evaluation
- [ ] Add OpenAI-based compatibility scoring
- [ ] Test with sample profiles from docs

### 1.3 Streamlit Dashboard v1
- [ ] User profile input form (using CURRENT_COFOUNDER_PROFILE.MD as template)
- [ ] Match criteria configuration
- [ ] Message template editor (using MATCH_MESSAGE_TEMPLATE.MD)
- [ ] Start/Stop controls
- [ ] Real-time event log display

## Phase 2: Autonomous Browsing (Week 2)

### 2.1 YC Site Navigation
- [ ] CUA login flow (manual first time, then automated)
- [ ] Navigate to cofounder matching page
- [ ] Scroll through profile list
- [ ] Click "View profile" for each candidate

### 2.2 Profile Extraction
- [ ] Screenshot profile pages
- [ ] Extract text from screenshots using CUA
- [ ] Parse profile sections (About, Background, Interests)
- [ ] Handle pagination and infinite scroll

### 2.3 Decision & Messaging
- [ ] Evaluate each profile against user criteria
- [ ] Generate match score and explanation
- [ ] Auto-fill message form with template
- [ ] Click "Invite to connect" for matches

## Phase 3: Safety & Persistence (Week 3)

### 3.1 Quota Management
- [ ] SQLite quota tracking (daily/weekly limits)
- [ ] Deduplication via profile hashing
- [ ] Stop flag implementation (.runs/stop.flag)
- [ ] Rate limiting between actions

### 3.2 Logging & Monitoring
- [ ] JSONL event logging with timestamps
- [ ] Session summaries (profiles viewed, matches found, messages sent)
- [ ] Error handling and retry logic
- [ ] Cost tracking (CUA token usage)

### 3.3 Testing & Refinement
- [ ] End-to-end test with real YC account
- [ ] Tune matching criteria thresholds
- [ ] Optimize CUA prompts for reliability
- [ ] Add fallback selectors for UI changes

## Technical Stack

### Core Dependencies
```python
# pyproject.toml additions
openai = "^1.0.0"  # For CUA via Responses API
python-dotenv = "^1.0.0"
streamlit = "^1.28.0"
pydantic = "^2.0.0"
pydantic-settings = "^2.0.0"
```

### CUA Configuration
```python
# CUA setup via Responses API
from openai import OpenAI

client = OpenAI()
response = client.responses.create(
    model="gpt-4o",  # CUA model when available
    messages=[...],
    tools=[{"type": "computer_use"}],
    temperature=0.3,
    max_tokens=4000
)
```

### File Structure Updates
```
src/yc_matcher/
├── domain/
│   ├── entities.py (ADD: UserProfile, MatchCriteria)
│   └── services.py (ADD: MatchingService)
├── infrastructure/
│   ├── cua_adapter.py (NEW: OpenAI CUA browser control)
│   └── browser_interface.py (NEW: CUA action handlers)
├── interface/
│   └── web/
│       └── ui_streamlit.py (REFACTOR: User profile focus)
```

## Migration Path

### From Current to Target State
1. **Keep existing infrastructure**: SQLite, JSONL logging, domain models
2. **Replace PlaywrightAdapter with CUAAdapter**: Simpler, AI-driven
3. **Flip UI perspective**: From "paste candidates" to "enter YOUR profile"
4. **Add autonomous loop**: CUA navigates and processes profiles automatically

### Backwards Compatibility
- Keep manual "paste & evaluate" mode as fallback
- Dual adapters: CUA for autonomous, Playwright for testing
- Feature flag: ENABLE_CUA=1 to activate new mode

## Success Criteria

### MVP Launch Ready When:
- [ ] CUA successfully navigates YC site autonomously
- [ ] Processes 10+ profiles without manual intervention
- [ ] Correctly identifies 8/10 good matches based on criteria
- [ ] Sends personalized messages without duplicates
- [ ] Total cost < $0.50 per 20-profile session

### Performance Targets
- Profile processing: < 30 seconds per profile
- Match evaluation: < 5 seconds per decision
- Message sending: < 10 seconds per invite
- Error rate: < 5% of actions require retry
- Token efficiency: < 1000 tokens per profile

## Risk Mitigation

### Technical Risks
- **CUA API limits**: Implement caching and batching
- **Site changes**: Use flexible selectors, add fallbacks
- **Rate limiting**: Add delays, respect site policies
- **Cost overruns**: Set token limits, monitor usage

### Operational Risks
- **Over-messaging**: Hard quota limits, deduplication
- **Poor matches**: Human review mode, adjustable thresholds
- **Account issues**: Start conservative, increase gradually
- **Debugging**: Comprehensive logging, screenshot saves

## Next Steps

1. **Immediate**: Create CUA adapter skeleton
2. **Tomorrow**: Test CUA with YC login flow
3. **This week**: Complete Phase 1 (core matching)
4. **Next week**: Phase 2 (autonomous browsing)
5. **Testing**: Real account trials with safety limits