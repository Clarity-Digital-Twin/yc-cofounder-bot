Architecture

## Principles
- **3-input control**: Your Profile + Match Criteria + Message Template
- **CUA-first architecture**: OpenAI CUA primary, Playwright fallback only
- **Provider agnostic**: Switch between OpenAI/Anthropic CUA via config
- **Local decision engine**: Evaluate matches locally, not in CUA
- **Clean DDD layers**: Ports define contracts, adapters implement them
- **Event-driven**: Every action logged as JSONL event stream

## Core Ports (Contracts)
- **ComputerUsePort**: `open(url)`, `click(selector)`, `read_text()`, `fill(field, text)`, `screenshot()`, `close()`
- **DecisionPort**: `evaluate(profile, criteria) → {score, decision, rationale}`
- **QuotaPort**: `check_remaining()`, `decrement()`, `reset()`
- **SeenRepo**: `is_duplicate(profile_hash)`, `mark_seen(profile_hash)`
- **LoggerPort**: `log_event(type, data)`
- **StopController**: `should_stop() → bool`

## Adapters (Implementations)
- **PRIMARY - CUA Adapters**:
  - `OpenAICUAAdapter`: Uses Responses API with computer-use-preview
  - `AnthropicCUAAdapter`: Uses Claude Computer Use API (optional)
- **FALLBACK - Browser Adapter**:
  - `PlaywrightBrowserAdapter`: Selector-based automation (when CUA unavailable)
- **Decision & Storage**:
  - `LocalDecisionAdapter`: Evaluates using rubric (not CUA)
  - `SQLiteQuotaRepo`: Daily/weekly limits
  - `SQLiteSeenRepo`: Deduplication database
  - `JSONLLogger`: Event stream to .jsonl files

## Execution Flow
1. **Input**: User provides 3 inputs via Streamlit
2. **Initialize**: Load config, select provider (CUA vs Playwright)
3. **Browse Loop**:
   - CUA/Playwright opens YC list
   - For each profile: navigate → read → evaluate locally
   - Decision: score > threshold?
   - If YES + quota available: auto-send message
4. **Events**: Log `decision`, `sent`, `stopped`, `model_usage`
5. **Termination**: Quota exhausted OR stop flag OR no more profiles

## Environment Configuration
```bash
# Provider Selection
ENABLE_CUA=1
CUA_PROVIDER=openai  # or 'anthropic'
CUA_API_KEY=sk-...
ENABLE_PLAYWRIGHT_FALLBACK=1

# Quotas & Pacing
DAILY_LIMIT=20
WEEKLY_LIMIT=60
SEND_DELAY_MS=5000

# YC Target
YC_MATCH_URL=https://www.startupschool.org/cofounder-matching
```

## Event Schema
```json
// decision event
{"type": "decision", "profile_id": "abc123", "score": 85, "decision": "YES", "rationale": "Strong ML background matches criteria"}

// sent event
{"type": "sent", "profile_id": "abc123", "ok": true, "mode": "auto", "verified": true}

// stopped event
{"type": "stopped", "reason": "user_requested"}

// model_usage event
{"type": "model_usage", "provider": "openai", "tokens_in": 1500, "tokens_out": 200, "cost_est": 0.0051}
```

## Provider Switching Logic
```python
# Pseudocode for adapter selection
if ENABLE_CUA and CUA_PROVIDER == "openai":
    adapter = OpenAICUAAdapter(api_key=CUA_API_KEY)
elif ENABLE_CUA and CUA_PROVIDER == "anthropic":
    adapter = AnthropicCUAAdapter(api_key=CUA_API_KEY)
elif ENABLE_PLAYWRIGHT_FALLBACK:
    adapter = PlaywrightBrowserAdapter()
else:
    raise ConfigError("No browser automation configured")
```

## Safety Mechanisms
- **STOP flag**: Check `.runs/stop.flag` before each action
- **Quotas**: Hard limits enforced at adapter level
- **Deduplication**: Never message same profile twice
- **Pacing**: Configurable delays between sends
- **Audit**: Complete JSONL trail of all decisions and actions
- **HIL Mode**: Optional human-in-the-loop approval before send