Architecture

## Principles
- **3-input control**: Your Profile + Match Criteria + Message Template
- **CUA+Playwright architecture**: CUA analyzes/plans, Playwright executes actions (they work TOGETHER)
- **Flexible decisions**: Three interchangeable modes (Advisor/Rubric/Hybrid)
- **OpenAI Computer Use**: Via Responses API - YOU provide browser via Playwright
- **Clean DDD layers**: Ports define contracts, adapters implement them
- **Event-driven**: Every action logged as JSONL event stream

## Core Ports (Contracts)

### ComputerUsePort
```python
open(url: str) -> None
find_click(locator: str) -> None  # CUA analyzes, Playwright clicks
read_text(target: str) -> str      # CUA extracts from screenshot
fill(selector: str, text: str) -> None  # CUA guides, Playwright types
press_send() -> None                # CUA locates, Playwright clicks
verify_sent() -> bool               # CUA analyzes result
screenshot() -> bytes               # Playwright captures for CUA
close() -> None
```

### DecisionPort
```python
evaluate(profile_text: str, criteria: Criteria) -> DecisionResult
# DecisionResult contains: mode, decision, rationale, extracted, scores
```

### Supporting Ports
- **QuotaPort**: `check_remaining()`, `decrement()`, `reset()`
- **SeenRepo**: `is_duplicate(profile_hash)`, `mark_seen(profile_hash)`
- **ProgressRepo**: `save_position()`, `load_position()`
- **LoggerPort**: `log_event(type, data)`
- **StopController**: `should_stop() -> bool`

## Decision Schema (Common for All Modes)

```json
{
  "mode": "advisor|rubric|hybrid",
  "decision": "YES|NO",
  "rationale": "≤120 chars explaining the decision",
  "extracted": {
    "name": "string?",
    "location": "string?",
    "tech_stack": ["python", "react", ...],
    "commitment": "ft|pt?",
    "stage": "idea|mvp|revenue?",
    "domain": "string?",
    "notes": "string?"
  },
  "scores": {
    "rubric_score": 0.0,      // 0-1, deterministic scoring
    "llm_confidence": 0.0,     // 0-1, AI confidence
    "final_score": 0.0         // 0-1, combined (hybrid only)
  },
  "prompt_ver": "v3.1",
  "rubric_ver": "r2.0",
  "criteria_hash": "sha256(criteria)"
}
```

## Decision Mode Details

### Advisor Mode (LLM-Only)
- Ask AI: "Given this profile and my criteria, is this a good match?"
- Returns: YES/NO + rationale
- Scores: Can be {0,0,0} or include llm_confidence if available
- Sending: NEVER auto-sends, requires HIL approval

### Rubric Gate Mode (Deterministic)
- Extract structured fields from profile
- Calculate rubric_score = Σ(weight_i * feature_i)
- Features:
  - Skill overlap (Jaccard similarity)
  - Location match (1.0 if match, 0.0 otherwise)
  - Commitment alignment (FT/PT match)
  - Stage compatibility
- Decision: YES if rubric_score ≥ THRESHOLD
- Sending: Auto-sends if YES + quota available

### Hybrid Mode (Combined)
- Calculate both rubric_score and llm_confidence
- final_score = α * llm_confidence + (1-α) * rubric_score
- Default α = 0.30 (30% AI, 70% rubric)
- Hard rules must pass (e.g., "must be full-time")
- Decision: YES if final_score ≥ THRESHOLD + hard rules pass
- Sending: Auto-sends if YES + quota available

## Adapters (Implementations)

### CUA Adapter (PRIMARY)
- **OpenAICUABrowser**: Computer Use tool via Agents SDK (env: `CUA_MODEL`)
  - Navigates YC, reads profile text from screen, clicks, types, verifies send

### Browser Adapter (FALLBACK)
- **PlaywrightBrowserAdapter**: Selector-based fallback (gated by `ENABLE_PLAYWRIGHT_FALLBACK=1`)

### Decision Adapters
- **AdvisorDecisionAdapter**: LLM evaluation
- **RubricDecisionAdapter**: Deterministic scoring
- **HybridDecisionAdapter**: Combined approach

### Storage Adapters
- **SQLiteQuotaRepo**: Daily/weekly limits enforcement
- **SQLiteSeenRepo**: Deduplication database
- **JSONLLogger**: Event stream to .jsonl files

## Execution Flow

1. **Initialize**:
   - Load 3 inputs + mode selection
   - Select provider (CUA vs Playwright)
   - Configure decision adapter per mode

2. **Browse Loop**:
   ```python
   while not should_stop() and quota_remaining() > 0:
       profile = cua.read_next_profile()
       if seen_repo.is_duplicate(profile.hash):
           continue
       
       decision = decision_port.evaluate(profile, criteria)
       logger.log_event("decision", decision)
       
       if decision.decision == "YES":
           if mode == "advisor":
               wait_for_hil_approval()
           elif quota_port.check_remaining() > 0:
               cua.fill_message(template.render(decision.extracted))
               if cua.press_send() and cua.verify_sent():
                   logger.log_event("sent", {"ok": true, "mode": "auto"})
                   quota_port.decrement()
                   seen_repo.mark_seen(profile.hash)
                   sleep(SEND_DELAY_MS)
   ```

3. **Termination**:
   - Stop flag set
   - Quota exhausted
   - No more profiles
   - Error threshold exceeded

## Event Schema

```json
// decision event
{
  "event": "decision",
  "mode": "hybrid",
  "decision": "YES",
  "rationale": "Strong ML background, local to SF",
  "scores": {
    "rubric_score": 0.78,
    "llm_confidence": 0.65,
    "final_score": 0.73
  },
  "criteria_hash": "abc123...",
  "prompt_ver": "v3.1",
  "rubric_ver": "r2.0",
  "extracted": {
    "name": "John Doe",
    "tech_stack": ["python", "tensorflow"],
    "location": "San Francisco"
  }
}

// sent event
{
  "event": "sent",
  "profile_id": "abc123",
  "ok": true,
  "mode": "auto",
  "chars": 312,
  "verified": true
}

// stopped event
{
  "event": "stopped",
  "reason": "user_requested"  // or "quota_exceeded", "error_threshold"
}

// model_usage event
{
  "event": "model_usage",
  "provider": "openai",
  "model": "<CUA_MODEL from env>",
  "tokens_in": 1500,
  "tokens_out": 200,
  "cost_est": 0.0051
}
```

## Provider Switching Logic

```python
def create_browser_adapter(config):
    if config.ENABLE_CUA:
        from infrastructure.openai_cua_browser import OpenAICUABrowser
        return OpenAICUABrowser(
            api_key=config.OPENAI_API_KEY,
            model=config.CUA_MODEL or os.getenv("CUA_MODEL"),  # read from env/config
            temperature=0.3
        )
    
    if config.ENABLE_PLAYWRIGHT_FALLBACK:
        return PlaywrightBrowserAdapter()
    
    raise ConfigError("No browser automation configured")

def create_decision_adapter(mode, config):
    if mode == "advisor":
        return AdvisorDecisionAdapter(config)
    elif mode == "rubric":
        return RubricDecisionAdapter(config)
    elif mode == "hybrid":
        return HybridDecisionAdapter(config, alpha=config.ALPHA)
    
    raise ConfigError(f"Unknown decision mode: {mode}")
```

## Implementation Notes

### Correct Import Pattern
```python
# Package name: openai-agents (pip install openai-agents)
# Import as: agents
from agents import Agent, ComputerTool, Session
```

### Environment Configuration
```bash
# Core
OPENAI_API_KEY=sk-...
ENABLE_CUA=1
CUA_MODEL=<your-computer-use-model>  # From Models endpoint

# Fallback
ENABLE_PLAYWRIGHT_FALLBACK=1

# Decision Engine
DECISION_MODE=advisor|rubric|hybrid
OPENAI_DECISION_MODEL=<your-best-llm>  # For Advisor/Hybrid
THRESHOLD=0.72
ALPHA=0.30  # Hybrid weighting (0..1)

# Safety & Limits
DAILY_QUOTA=25
WEEKLY_QUOTA=120
SEND_DELAY_MS=5000
SHADOW_MODE=0  # 1 = evaluate-only

# Paths
RUNS_DIR=.runs
EVENTS_FILE=events.jsonl
```

## Safety Mechanisms
- **STOP flag**: Check `.runs/stop.flag` before each action
- **Quotas**: Hard limits enforced at adapter level
- **Deduplication**: Never message same profile twice
- **Pacing**: Configurable delays between sends
- **Shadow Mode**: Evaluate-only, no sends
- **HIL Mode**: Manual approval required (Advisor mode)
- **Audit**: Complete JSONL trail with versioning

## Invariants
- If `STOP` flag exists → abort before any send
- Never send if `seen` already contains candidate key
- Never exceed daily/weekly quotas
- Always log `decision` before any `sent`
- CUA is primary; Playwright only if CUA disabled or fails and fallback enabled
