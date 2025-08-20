# OpenAI Computer Use Guide

## Overview
OpenAI's Computer Use tool (via the Agents SDK) enables applications to interact with computer interfaces through screenshots and simulated actions. This guide covers implementing OpenAI's Computer-Using Agent (CUA) model for browser automation in the YC Cofounder Matching Bot.

## Availability
- **Access**: Research preview - check your account's Models endpoint for availability
- **Status**: Research preview
- **API**: Computer Use tool via OpenAI Agents SDK
- **Model**: Computer-Using Agent (CUA) - verify availability at platform.openai.com/account/models

## Pricing
- Computer Use is billed at your model's standard token rates
- Some tools may have additional per-call charges
- **Do not hardcode prices** - consult [OpenAI Pricing](https://openai.com/api/pricing/) for current rates
- Monitor actual usage via your account dashboard

## How It Works

### Core Architecture
1. **Agents SDK** orchestrates the workflow
2. **Computer Use tool** (hosted) captures screenshots and executes actions
3. **CUA model** analyzes UI and determines actions
4. Computer Use runs in OpenAI's hosted environment (no local browser needed)

### Integration Flow
```
Application → OpenAI Agents SDK → Computer Use Tool (Hosted) → CUA Model → Actions
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
from agents import Agent, ComputerTool, Runner
import os

# Initialize agent with Computer Use tool
agent = Agent(
    name="CUA Agent",
    model=os.getenv("CUA_MODEL"),  # From your Models endpoint
    tools=[ComputerTool()],
    temperature=0.3  # Low for determinism
)
```

### 3. Execute Browser Actions
```python
async def navigate_and_extract(agent, url):
    """Use Computer Use to navigate and extract profile."""
    result = await Runner.run(
        agent,
        f"Navigate to {url} and extract profile text"
    )
    return result.final_output

# Synchronous version
def navigate_and_extract_sync(agent, url):
    result = Runner.run_sync(
        agent,
        f"Navigate to {url} and extract profile text"
    )
    return result.final_output
```

## YC Matcher Integration

### OpenAICUABrowser Implementation
```python
from agents import Agent, ComputerTool, Runner
from typing import Optional
import os

class OpenAICUABrowser:
    """Browser automation via OpenAI Computer Use (Agents SDK)."""
    
    def __init__(self):
        self.agent = Agent(
            name="YC Browser",
            model=os.getenv("CUA_MODEL"),  # From your Models endpoint
            tools=[ComputerTool()],
            temperature=0.3,
            instructions="You are browsing YC Cofounder Matching. Be precise and efficient."
        )
    
    async def browse_to_profile(self, url: str) -> dict:
        """Navigate to profile and extract data."""
        result = await Runner.run(
            self.agent,
            f"Navigate to {url} and extract all visible profile information"
        )
        return self._parse_profile(result.final_output)
    
    async def send_message(self, message: str) -> bool:
        """Fill message box and send."""
        result = await Runner.run(
            self.agent,
            f"Fill the message box with this text and click send: {message}"
        )
        return self._verify_sent(result.final_output)
    
    def _parse_profile(self, output: str) -> dict:
        """Parse extracted profile text into structured data."""
        # Implementation specific to your needs
        return {"raw_text": output}
    
    def _verify_sent(self, output: str) -> bool:
        """Verify message was sent successfully."""
        return "sent" in output.lower() or "success" in output.lower()
```

## Configuration

### Environment Variables
```bash
# Core Settings
ENABLE_CUA=1
CUA_MODEL=<your-computer-use-model>     # From Models endpoint
OPENAI_API_KEY=sk-...

# Decision Engine (separate from CUA)
OPENAI_DECISION_MODEL=<your-best-llm>   # For Advisor/Hybrid evaluation
DECISION_MODE=advisor|rubric|hybrid

# Safety & Limits
DAILY_QUOTA=25
WEEKLY_QUOTA=120
SEND_DELAY_MS=5000
THRESHOLD=0.72

# Fallback
ENABLE_PLAYWRIGHT_FALLBACK=1
```

## Model Selection
- **CUA Model**: Set `CUA_MODEL` to a Computer Use-enabled model from your account
  - Check https://platform.openai.com/account/models
  - Look for models with Computer Use capability
  - Update when newer models become available
- **Decision Model**: Set `OPENAI_DECISION_MODEL` for reasoning/evaluation
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
if not quota.check_and_increment():
    logger.emit({"event": "quota_exceeded"})
    return False
```

### Action Verification
```python
# After send action
result = await Runner.run(agent, "Verify the message was sent")
if "success" not in result.final_output.lower():
    # Retry once
    result = await Runner.run(agent, "Click send button again")
    if "success" not in result.final_output.lower():
        logger.emit({"event": "send_failed"})
        return False
```

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
   - Monitor token usage via dashboard

4. **Testing**
   - Contract tests for BrowserPort
   - Integration tests with mock responses
   - Manual HIL testing on real site

## Session Memory (Optional)

For maintaining context across multiple interactions:
```python
from agents import SQLiteSession

# Create persistent session
session = SQLiteSession("yc_browser_session")

# Use session for memory
result = await Runner.run(
    agent,
    "Navigate to next profile",
    session=session  # Remembers previous context
)
```

## Migration from Manual Flow

1. **Phase 1**: Add OpenAICUABrowser alongside existing
2. **Phase 2**: Feature flag to toggle between modes
3. **Phase 3**: Gradual rollout with monitoring
4. **Phase 4**: Deprecate manual paste workflow

## Resources
- [OpenAI Agents SDK Docs](https://openai.github.io/openai-agents-python/)
- [Running Agents Guide](https://openai.github.io/openai-agents-python/running_agents/)
- [Models Endpoint](https://platform.openai.com/account/models)
- [API Pricing](https://openai.com/api/pricing/)