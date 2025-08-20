# OpenAI Computer Use Guide

## Overview
OpenAI's Computer Use tool (via the Agents SDK) enables applications to interact with computer interfaces through screenshots and simulated actions. This guide covers implementing OpenAI's Computer-Using Agent (CUA) model for browser automation in the YC Cofounder Matching Bot.

## Availability
- **Access**: Available for developers in usage tiers 3-5
- **Status**: Research preview
- **API**: Computer Use tool via OpenAI Agents SDK
- **Model**: Computer-Using Agent (CUA) - check Models endpoint for availability

## Pricing
- **Input**: $3 per 1M tokens
- **Output**: $12 per 1M tokens
- Billed at CUA model rates through the Computer Use tool

## How It Works

### Core Architecture
1. **Agents SDK** orchestrates the workflow
2. **Computer Use tool** captures screenshots and executes actions
3. **CUA model** analyzes UI and determines actions
4. Your code implements the browser/VM environment

### Integration Flow
```
Application → OpenAI Agents SDK → Computer Use Tool → CUA Model → Actions → Browser
```

### Available Actions
- `click(x, y)` - Click at specific coordinates
- `type(text)` - Type text input
- `scroll(direction, amount)` - Scroll actions
- `navigate(url)` - Navigate to URLs
- `screenshot()` - Capture current state

## Implementation

### 1. Install OpenAI Agents SDK
```bash
pip install openai-agents
```

### 2. Initialize Agent with Computer Use
```python
from openai_agents import Agent, ComputerTool
import os

# Initialize agent with Computer Use tool
agent = Agent(
    model=os.getenv("CUA_MODEL", "computer-use-preview"),
    tools=[ComputerTool()],
    temperature=0.3  # Low for determinism
)
```

### 3. Execute Browser Actions
```python
def navigate_and_extract(agent, url):
    """Use Computer Use to navigate and extract profile."""
    result = agent.run(
        messages=[
            {"role": "user", "content": f"Navigate to {url} and extract profile text"}
        ],
        tools=[ComputerTool()]
    )
    return result
```

## YC Matcher Integration

### OpenAICUAAdapter Implementation
```python
class OpenAICUAAdapter:
    """Adapter implementing ComputerUsePort via OpenAI Agents SDK."""
    
    def __init__(self):
        from openai_agents import Agent, ComputerTool
        self.agent = Agent(
            model=os.getenv("CUA_MODEL", "computer-use-preview"),
            tools=[ComputerTool()],
            temperature=0.3
        )
    
    def browse_to_profile(self, url: str) -> ProfileData:
        """Navigate to profile and extract data."""
        result = self.agent.run(
            messages=[{"role": "user", "content": f"Navigate to {url} and extract profile"}],
            tools=[ComputerTool()]
        )
        return self._parse_profile(result)
    
    def send_message(self, message: str) -> bool:
        """Fill message box and send."""
        result = self.agent.run(
            messages=[{"role": "user", "content": f"Fill message box with: {message} and click send"}],
            tools=[ComputerTool()]
        )
        return self._verify_sent(result)
```

## Configuration

### Environment Variables
```bash
# Core Settings
ENABLE_CUA=1
CUA_PROVIDER=openai
CUA_MODEL=computer-use-preview  # Or latest from Models endpoint
OPENAI_API_KEY=sk-...

# Decision Engine (separate from CUA)
DECISION_MODEL=gpt-4-turbo  # For Advisor/Hybrid evaluation
DECISION_MODE=advisor|rubric|hybrid

# Safety & Limits
DAILY_LIMIT=10
WEEKLY_LIMIT=50
SEND_DELAY_MS=1000
THRESHOLD=0.72

# Fallback
ENABLE_PLAYWRIGHT_FALLBACK=1
```

## Model Selection
- **CUA Model**: Set `CUA_MODEL` to your account's computer-use model
  - Check https://platform.openai.com/account/models
  - Default: `computer-use-preview`
  - Future: Update when newer models available (e.g., GPT-5 CUA)
- **Decision Model**: Set `DECISION_MODEL` for reasoning/evaluation
  - Separate from CUA - handles Advisor/Hybrid logic
  - Use your best available reasoning model

## Safety Implementation

### STOP Flag Integration
```python
if stop_controller.is_stopped():
    logger.emit({"event": "stopped"})
    return
```

### Quota Enforcement
```python
if not quota.check_and_increment(daily_limit):
    logger.emit({"event": "quota_block"})
    return False
```

### Action Verification
```python
# After send action
if not verify_sent():
    # Retry once
    agent.run(messages=[{"role": "user", "content": "Click send again"}])
    if not verify_sent():
        logger.emit({"event": "send_failed"})
        return False
```

## Performance
- **WebArena**: 58.1% success rate
- **WebVoyager**: 87% success rate
- **OSWorld**: 38.1% for full computer tasks
- **Recommendation**: Keep human-in-loop for critical actions

## Best Practices

1. **Temperature Control**
   - Use 0.2-0.4 for deterministic actions
   - Higher only for creative tasks

2. **Fallback Strategy**
   - Keep Playwright as backup
   - Auto-switch on CUA errors

3. **Monitoring**
   - Log all CUA actions
   - Track success rates
   - Monitor token usage

4. **Testing**
   - Contract tests for ComputerUsePort
   - Integration tests with mock browser
   - E2E smoke tests on real YC site

## Migration from Manual Flow

1. **Phase 1**: Add OpenAICUAAdapter alongside existing
2. **Phase 2**: Feature flag to toggle between modes
3. **Phase 3**: Gradual rollout with monitoring
4. **Phase 4**: Deprecate manual paste workflow

## Resources
- [OpenAI Computer Use Docs](https://platform.openai.com/docs/guides/tools-computer-use)
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [Models Endpoint](https://platform.openai.com/account/models)