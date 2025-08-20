# OpenAI Computer Use Technical Implementation Guide

## Architecture Overview

### System Components
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│ CUA Browser  │────▶│ OpenAI Agents   │
│   (3 inputs)    │     │   Adapter    │     │ SDK + CUA Tool  │
└─────────────────┘     └──────────────┘     └─────────────────┘
                              │                       │
                              ▼                       ▼
                     ┌──────────────────┐    ┌────────────────┐
                     │ Hosted Computer  │◀───│ Computer Use   │
                     │ Environment      │    │ Actions        │
                     └──────────────────┘    └────────────────┘
```

**Note**: Computer Use runs in OpenAI's **hosted environment** - no local browser setup required for CUA.

## 1. SDK Installation and Setup

### Install Dependencies
```bash
pip install openai-agents
# Note: pyautogui/pillow only needed for Playwright fallback, not CUA
```

### Initialize OpenAI Agents
```python
from agents import Agent, ComputerTool, Runner
import os

class OpenAICUABrowser:
    def __init__(self):
        # Use Computer-Using Agent model via env
        self.model = os.getenv("CUA_MODEL")  # From your Models endpoint
        
        # Initialize agent with Computer Use tool
        self.agent = Agent(
            name="YC Browser",
            model=self.model,
            tools=[ComputerTool()],
            temperature=0.3,  # Low for determinism
            instructions="Navigate YC Cofounder Matching precisely and efficiently."
        )
```

## 2. Computer Use Tool Integration

### Browser Navigation
```python
async def navigate_to_profile(self, url: str) -> dict:
    """Navigate to YC profile using Computer Use tool"""
    
    result = await Runner.run(
        self.agent,
        f"Navigate to {url} and wait for page to fully load"
    )
    
    return {"success": True, "output": result.final_output}
```

### Profile Extraction
```python
async def extract_profile_data(self) -> dict:
    """Extract profile information via Computer Use"""
    
    result = await Runner.run(
        self.agent,
        "Extract all visible profile text including name, skills, location, and bio"
    )
    
    # Parse extracted data
    return self._parse_profile(result.final_output)
```

### Message Sending
```python
async def send_message(self, message_text: str) -> bool:
    """Fill and send message using Computer Use"""
    
    prompt = f"""
    1. Click on the message input box
    2. Type the following message exactly: {message_text}
    3. Click the Send/Invite button
    4. Verify the message was sent successfully
    """
    
    result = await Runner.run(self.agent, prompt)
    
    return self._verify_sent(result.final_output)
```

## 3. Session Memory (Optional)

For maintaining context across multiple profile visits:

```python
from agents import SQLiteSession

class OpenAICUABrowser:
    def __init__(self):
        self.agent = Agent(
            name="YC Browser",
            model=os.getenv("CUA_MODEL"),
            tools=[ComputerTool()]
        )
        # Optional: Use session for memory
        self.session = SQLiteSession("yc_browsing_session")
    
    async def browse_next_profile(self):
        """Browse to next profile with context memory"""
        result = await Runner.run(
            self.agent,
            "Click on the next profile in the list",
            session=self.session  # Remembers previous profiles
        )
        return result.final_output
```

## 4. Complete Implementation

### Full OpenAICUABrowser
```python
from agents import Agent, ComputerTool, Runner
from typing import Dict, Optional, List
import os
import asyncio

class OpenAICUABrowser:
    """OpenAI Computer Use browser for YC Matcher"""
    
    def __init__(self):
        self.model = os.getenv("CUA_MODEL")  # From your Models endpoint
        self.agent = Agent(
            name="YC Browser",
            model=self.model,
            tools=[ComputerTool()],
            temperature=0.3,
            instructions="You are browsing YC Cofounder Matching. Be precise and efficient."
        )
    
    async def browse_profiles(self, base_url: str, criteria: Dict) -> List[Dict]:
        """Main workflow: browse profiles autonomously"""
        profiles = []
        
        # Navigate to listing
        await Runner.run(
            self.agent,
            f"Navigate to {base_url} and wait for the profile list to load"
        )
        
        # Iterate through profiles
        for i in range(criteria.get('max_profiles', 10)):
            # Check STOP flag
            if self._should_stop():
                break
            
            # Click on profile
            result = await Runner.run(
                self.agent,
                f"Click on profile number {i+1} in the list"
            )
            
            # Extract data
            profile_data = await self.extract_profile_data()
            profiles.append(profile_data)
            
            # Evaluate with decision engine
            decision = await self._evaluate(profile_data, criteria)
            
            if decision['should_message']:
                # Send message
                sent = await self.send_message(decision['message'])
                profile_data['sent'] = sent
            
            # Go back to list
            await Runner.run(
                self.agent,
                "Go back to the profile list"
            )
            
            # Respect pacing
            await asyncio.sleep(int(os.getenv("SEND_DELAY_MS", "5000")) / 1000)
        
        return profiles
    
    async def extract_profile_data(self) -> Dict:
        """Extract profile from current page"""
        result = await Runner.run(
            self.agent,
            "Extract the profile name, skills, location, and bio from the current page"
        )
        
        return self._parse_profile(result.final_output)
    
    async def send_message(self, text: str) -> bool:
        """Send a message to current profile"""
        result = await Runner.run(
            self.agent,
            f"Click the message box, type this message, then click send: {text}"
        )
        
        # Verify sent
        verify_result = await Runner.run(
            self.agent,
            "Check if the message was sent successfully"
        )
        
        return "success" in verify_result.final_output.lower()
    
    def _parse_profile(self, text: str) -> Dict:
        """Parse profile text into structured data"""
        # Implementation specific to your extraction needs
        return {
            "raw_text": text,
            "extracted": True
        }
    
    async def _evaluate(self, profile: Dict, criteria: Dict) -> Dict:
        """Evaluate profile using decision mode"""
        mode = os.getenv("DECISION_MODE", "advisor")
        
        if mode == "advisor":
            # Use LLM evaluation (separate from CUA)
            return await self._advisor_evaluate(profile, criteria)
        elif mode == "rubric":
            # Use deterministic rules
            return self._rubric_evaluate(profile, criteria)
        elif mode == "hybrid":
            # Combine both
            advisor = await self._advisor_evaluate(profile, criteria)
            rubric = self._rubric_evaluate(profile, criteria)
            return self._combine_decisions(advisor, rubric)
        
        return {"should_message": False}
    
    def _should_stop(self) -> bool:
        """Check if STOP flag is set"""
        return os.path.exists(".runs/stop.flag")
```

## 5. Integration with Existing Code

### Port Implementation
```python
# application/ports.py
from typing import Protocol

class BrowserPort(Protocol):
    """Port for browser automation"""
    
    async def browse_profiles(self, url: str, criteria: Dict) -> List[Dict]: ...
    async def extract_profile_data(self) -> Dict: ...
    async def send_message(self, text: str) -> bool: ...
```

### Dependency Injection
```python
# interface/di.py
def build_browser():
    if os.getenv("ENABLE_CUA") == "1":
        from infrastructure.openai_cua_browser import OpenAICUABrowser
        return OpenAICUABrowser()
    elif os.getenv("ENABLE_PLAYWRIGHT_FALLBACK") == "1":
        from infrastructure.browser_playwright import PlaywrightBrowser
        return PlaywrightBrowser()
    else:
        raise ValueError("No browser adapter configured")
```

## 6. Playwright Fallback Setup

**Note**: This section only applies to the Playwright fallback, NOT to CUA.

```python
# infrastructure/browser_playwright.py
import subprocess
from playwright.async_api import async_playwright

class PlaywrightBrowser:
    """Fallback browser using Playwright (when CUA unavailable)"""
    
    def __init__(self):
        self.browser = None
        self.page = None
    
    async def start(self):
        """Launch local browser for Playwright"""
        # For headless operation with Playwright (NOT CUA)
        if os.getenv("PLAYWRIGHT_HEADLESS") == "1":
            # Optional: Setup Xvfb for headless
            subprocess.run(['Xvfb', ':99', '-screen', '0', '1280x800x24'], 
                          check=False, capture_output=True)
            os.environ['DISPLAY'] = ':99'
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=os.getenv("PLAYWRIGHT_HEADLESS") == "1"
        )
        self.page = await self.browser.new_page()
```

## 7. Testing Strategy

### Contract Tests
```python
# tests/contracts/test_browser_port.py
import pytest
from unittest.mock import AsyncMock

class TestBrowserPortContract:
    @pytest.mark.asyncio
    async def test_browse_profiles(self, mock_browser):
        """Test browser can browse profiles"""
        profiles = await mock_browser.browse_profiles(
            "https://yc.test", 
            {"max_profiles": 5}
        )
        assert len(profiles) <= 5
    
    @pytest.mark.asyncio
    async def test_extract_profile(self, mock_browser):
        """Test profile extraction"""
        data = await mock_browser.extract_profile_data()
        assert "raw_text" in data
    
    @pytest.mark.asyncio
    async def test_send_message(self, mock_browser):
        """Test message sending"""
        sent = await mock_browser.send_message("Hello!")
        assert isinstance(sent, bool)
```

### Integration Tests
```python
# tests/integration/test_cua_flow.py
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_cua_flow():
    """Test complete CUA workflow"""
    browser = OpenAICUABrowser()
    
    profiles = await browser.browse_profiles(
        "https://yc-test.local",
        {"max_profiles": 2}
    )
    assert len(profiles) <= 2
```

## 8. Configuration Reference

### Environment Variables
```bash
# OpenAI Computer Use
ENABLE_CUA=1
CUA_MODEL=<your-computer-use-model>     # From Models endpoint
OPENAI_API_KEY=sk-...

# Decision Engine (separate from CUA)
OPENAI_DECISION_MODEL=<your-best-llm>   # For Advisor/Hybrid
DECISION_MODE=advisor|rubric|hybrid
THRESHOLD=0.72
ALPHA=0.50

# Safety
DAILY_QUOTA=25
WEEKLY_QUOTA=120
SEND_DELAY_MS=5000

# Fallback
ENABLE_PLAYWRIGHT_FALLBACK=1

# YC Config
YC_MATCH_URL=https://www.startupschool.org/cofounder-matching
```

## 9. Model Management

### Checking Available Models
```python
# Check your available models at:
# https://platform.openai.com/account/models

# Or via API:
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")
models = openai.models.list()
cua_models = [m for m in models if "computer-use" in m.id.lower()]
```

### Model Upgrade Process
1. Check Models endpoint for new Computer Use models
2. Update `CUA_MODEL` in `.env`
3. Run contract tests: `pytest tests/contracts/`
4. Run integration smoke test
5. Compare metrics (success rate, latency, cost)
6. If issues, revert `CUA_MODEL` to previous

## 10. Performance Optimization

### Token Usage
- Keep prompts concise and specific
- Batch related actions when possible
- Use low temperature (0.2-0.4) for consistency

### Latency
- Reuse agent instance across requests
- Implement timeout handling
- Use session memory to avoid repeated context

### Cost Management
- Monitor via `model_usage` events
- Set hard limits in quota system
- Use rubric mode for initial filtering
- Only use CUA for qualified profiles

## 11. Troubleshooting

### Common Issues

1. **"Model not available"**
   - Check your account's Models endpoint
   - Verify API key has correct permissions
   - Confirm you have access to Computer Use models

2. **"Computer Use action failed"**
   - Increase action delay in prompts
   - Add verification steps
   - Check for rate limits

3. **"High token usage"**
   - Keep prompts concise
   - Batch multiple actions
   - Monitor usage in dashboard

4. **"Inconsistent results"**
   - Lower temperature to 0.2-0.3
   - Add explicit instructions
   - Use verification steps

## Resources
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [Running Agents](https://openai.github.io/openai-agents-python/running_agents/)
- [Tools Documentation](https://openai.github.io/openai-agents-python/tools/)
- [Models Endpoint](https://platform.openai.com/account/models)
- [API Pricing](https://openai.com/api/pricing/)