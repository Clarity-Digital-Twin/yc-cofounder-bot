# OpenAI Computer Use Technical Implementation Guide

## Architecture Overview

### System Components
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│  CUA Adapter │────▶│ OpenAI Agents   │
│   (3 inputs)    │     │   (OpenAI)   │     │ SDK + CUA Tool  │
└─────────────────┘     └──────────────┘     └─────────────────┘
                              │                       │
                              ▼                       ▼
                     ┌──────────────────┐    ┌────────────────┐
                     │ Browser/VM       │◀───│ Computer Use   │
                     │ Environment      │    │ Actions        │
                     └──────────────────┘    └────────────────┘
```

## 1. SDK Installation and Setup

### Install Dependencies
```bash
pip install openai-agents pillow pyautogui
```

### Initialize OpenAI Agents
```python
from agents import Agent, ComputerTool, Session
import os

class OpenAICUAAdapter:
    def __init__(self):
        # Use Computer-Using Agent model via env
        self.model = os.getenv("CUA_MODEL")  # From your Models endpoint
        
        # Initialize agent with Computer Use tool
        self.agent = Agent(
            model=self.model,
            tools=[ComputerTool()],
            temperature=0.3  # Low for determinism
        )
        
        # Session for maintaining context
        self.session = Session()
    
    def initialize_session(self):
        """Start a new browser automation session"""
        self.session = Session()
        return self
```

## 2. Computer Use Tool Integration

### Browser Navigation
```python
def navigate_to_profile(self, url: str) -> Dict:
    """Navigate to YC profile using Computer Use tool"""
    
    result = self.agent.run(
        messages=[
            {
                "role": "system", 
                "content": "You are navigating YC cofounder matching. Be precise."
            },
            {
                "role": "user",
                "content": f"Navigate to {url} and wait for page load"
            }
        ],
        tools=[ComputerTool()],
        session=self.session
    )
    
    return result
```

### Profile Extraction
```python
def extract_profile_data(self) -> Dict:
    """Extract profile information via Computer Use"""
    
    result = self.agent.run(
        messages=[
            {
                "role": "user",
                "content": "Extract all visible profile text including name, skills, location, and bio"
            }
        ],
        tools=[ComputerTool()],
        session=self.session
    )
    
    # Parse extracted data
    return self._parse_profile(result)
```

### Message Sending
```python
def send_message(self, message_text: str) -> bool:
    """Fill and send message using Computer Use"""
    
    result = self.agent.run(
        messages=[
            {
                "role": "user",
                "content": f"""
                1. Click on the message input box
                2. Type the following message: {message_text}
                3. Click the Send/Invite button
                4. Verify the message was sent
                """
            }
        ],
        tools=[ComputerTool()],
        session=self.session
    )
    
    return self._verify_sent(result)
```

## 3. Environment Setup for Computer Use

### Local Browser/VM Configuration
```python
import subprocess
from pathlib import Path

class BrowserEnvironment:
    """Manages browser environment for Computer Use"""
    
    def __init__(self):
        self.browser_process = None
        self.display_size = (1280, 800)
    
    def start(self):
        """Launch browser in controlled environment"""
        # For headless operation
        env = os.environ.copy()
        env['DISPLAY'] = ':99'  # Virtual display
        
        # Start Xvfb for headless
        subprocess.run(['Xvfb', ':99', '-screen', '0', '1280x800x24'], 
                      check=False, capture_output=True)
        
        # Launch browser
        self.browser_process = subprocess.Popen(
            ['chromium', '--no-sandbox', '--disable-dev-shm-usage'],
            env=env
        )
    
    def stop(self):
        """Clean up browser environment"""
        if self.browser_process:
            self.browser_process.terminate()
```

## 4. Complete Implementation

### Full OpenAICUAAdapter
```python
from agents import Agent, ComputerTool, Session
from typing import Dict, Optional
import os
import time

class OpenAICUAAdapter:
    """OpenAI Computer Use adapter for YC Matcher"""
    
    def __init__(self):
        self.model = os.getenv("CUA_MODEL")  # From your Models endpoint
        self.agent = Agent(
            model=self.model,
            tools=[ComputerTool()],
            temperature=0.3
        )
        self.session = Session()
        self.environment = BrowserEnvironment()
    
    def start(self):
        """Initialize browser and session"""
        self.environment.start()
        self.session = Session()
        time.sleep(2)  # Wait for browser
        return self
    
    def browse_profiles(self, base_url: str, criteria: Dict) -> list:
        """Main workflow: browse profiles autonomously"""
        profiles = []
        
        # Navigate to listing
        self.agent.run(
            messages=[{"role": "user", "content": f"Navigate to {base_url}"}],
            tools=[ComputerTool()],
            session=self.session
        )
        
        # Iterate through profiles
        for i in range(criteria.get('max_profiles', 10)):
            # Check STOP flag
            if self._should_stop():
                break
            
            # Click on profile
            result = self.agent.run(
                messages=[{"role": "user", "content": f"Click on profile #{i+1}"}],
                tools=[ComputerTool()],
                session=self.session
            )
            
            # Extract data
            profile_data = self.extract_profile_data()
            profiles.append(profile_data)
            
            # Evaluate with decision engine
            decision = self._evaluate(profile_data, criteria)
            
            if decision['should_message']:
                # Send message
                sent = self.send_message(decision['message'])
                profile_data['sent'] = sent
            
            # Go back to list
            self.agent.run(
                messages=[{"role": "user", "content": "Go back to profile list"}],
                tools=[ComputerTool()],
                session=self.session
            )
        
        return profiles
    
    def _evaluate(self, profile: Dict, criteria: Dict) -> Dict:
        """Evaluate profile using decision mode"""
        mode = os.getenv("DECISION_MODE", "advisor")
        
        if mode == "advisor":
            # Use LLM evaluation
            return self._advisor_evaluate(profile, criteria)
        elif mode == "rubric":
            # Use deterministic rules
            return self._rubric_evaluate(profile, criteria)
        elif mode == "hybrid":
            # Combine both
            advisor = self._advisor_evaluate(profile, criteria)
            rubric = self._rubric_evaluate(profile, criteria)
            return self._combine_decisions(advisor, rubric)
        
        return {"should_message": False}
    
    def cleanup(self):
        """Stop browser and clean up"""
        self.environment.stop()
```

## 5. Integration with Existing Code

### Port Implementation
```python
# application/ports.py
from typing import Protocol

class ComputerUsePort(Protocol):
    """Port for computer/browser automation"""
    
    def start(self) -> None: ...
    def browse_profiles(self, url: str, criteria: Dict) -> list: ...
    def extract_profile_data(self) -> Dict: ...
    def send_message(self, text: str) -> bool: ...
    def cleanup(self) -> None: ...
```

### Dependency Injection
```python
# interface/di.py
def build_services():
    if os.getenv("ENABLE_CUA") == "1":
        from infrastructure.openai_cua import OpenAICUAAdapter
        browser = OpenAICUAAdapter()
    elif os.getenv("ENABLE_PLAYWRIGHT_FALLBACK") == "1":
        from infrastructure.browser_playwright import PlaywrightBrowser
        browser = PlaywrightBrowser()
    else:
        raise ValueError("No browser adapter configured")
    
    return browser
```

## 6. Testing Strategy

### Contract Tests
```python
# tests/contracts/test_computer_use_port.py
import pytest
from unittest.mock import Mock

class TestComputerUseContract:
    def test_browse_profiles(self, mock_cua):
        """Test CUA can browse profiles"""
        mock_cua.browse_profiles("https://yc.test", {"max": 5})
        assert mock_cua.session.message_count > 0
    
    def test_extract_profile(self, mock_cua):
        """Test profile extraction"""
        data = mock_cua.extract_profile_data()
        assert "name" in data
        assert "skills" in data
    
    def test_send_message(self, mock_cua):
        """Test message sending"""
        sent = mock_cua.send_message("Hello!")
        assert isinstance(sent, bool)
```

### Integration Tests
```python
# tests/integration/test_cua_flow.py
@pytest.mark.integration
def test_full_cua_flow():
    """Test complete CUA workflow"""
    adapter = OpenAICUAAdapter()
    adapter.start()
    
    try:
        profiles = adapter.browse_profiles(
            "https://yc-test.local",
            {"max_profiles": 2, "criteria": "Python"}
        )
        assert len(profiles) <= 2
    finally:
        adapter.cleanup()
```

## 7. Configuration Reference

### Environment Variables
```bash
# OpenAI Computer Use
ENABLE_CUA=1
CUA_PROVIDER=openai
CUA_MODEL=<your account's computer-use model>  # From Models endpoint
OPENAI_API_KEY=sk-...

# Decision Engine
DECISION_MODEL=gpt-4-turbo  # For Advisor/Hybrid
DECISION_MODE=advisor|rubric|hybrid
THRESHOLD=0.72
ALPHA=0.30

# Safety
DAILY_LIMIT=10
WEEKLY_LIMIT=50
SEND_DELAY_MS=1000
STRICT_RULES=1

# Fallback
ENABLE_PLAYWRIGHT_FALLBACK=1

# YC Config
YC_MATCH_URL=https://www.startupschool.org/cofounder-matching
```

## 8. Model Upgrade Checklist
1. Check Models endpoint for new Computer Use models
2. Update `CUA_MODEL` in `.env`
3. Run contract tests: `pytest tests/contracts/`
4. Run integration smoke test
5. Compare metrics (success rate, latency, cost)
6. If issues, revert `CUA_MODEL` to previous

## 9. Performance Optimization

### Token Usage
- Resize screenshots to 1280x800
- Use "low" detail for simple navigation
- Use "high" detail for text extraction
- Batch instructions when possible

### Latency
- Keep temperature at 0.2-0.4
- Cache session context
- Reuse agent instance
- Implement timeout handling

### Cost Management
- Monitor via `model_usage` events
- Set hard limits in quota system
- Use rubric mode for initial filtering
- Only use CUA for qualified profiles

## 10. Troubleshooting

### Common Issues

1. **"Model not available"**
   - Check tier access (needs tier 3-5)
   - Verify model name at Models endpoint
   - Ensure API key has correct permissions

2. **"Screenshot capture failed"**
   - Install display dependencies
   - Check virtual display (Xvfb) running
   - Verify browser launched correctly

3. **"Actions not executing"**
   - Increase action delay
   - Add verification steps
   - Check browser responsiveness

4. **"High token usage"**
   - Reduce screenshot resolution
   - Use "low" detail mode
   - Batch multiple actions

## Resources
- [OpenAI Computer Use Guide](https://platform.openai.com/docs/guides/tools-computer-use)
- [OpenAI Agents SDK Docs](https://openai.github.io/openai-agents-python/)
- [Models Endpoint](https://platform.openai.com/account/models)
- [Tier Access](https://platform.openai.com/account/limits)