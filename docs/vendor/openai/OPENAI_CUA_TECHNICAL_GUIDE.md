# OpenAI Computer Use Technical Implementation Guide

## Architecture Overview

### System Components
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│ CUA Browser  │────▶│ OpenAI          │
│   (3 inputs)    │     │   Adapter    │     │ Responses API   │
└─────────────────┘     └──────────────┘     └─────────────────┘
                              │                       │
                              ▼                       ▼
                     ┌──────────────────┐    ┌────────────────┐
                     │ YOUR Playwright  │◀───│ CUA Suggests   │
                     │ Browser Instance │    │ Actions        │
                     └──────────────────┘    └────────────────┘
```

**CRITICAL**: YOU provide the browser via Playwright. CUA only analyzes screenshots and suggests actions.

## 1. How Computer Use ACTUALLY Works

### The Truth
- **YOU provide the browser** (Playwright, Selenium, etc.)
- **YOU execute actions** (clicks, typing, scrolling)
- **YOU take screenshots** and send them to CUA
- **CUA analyzes** screenshots and suggests next actions
- **YOU loop** until task complete

### What CUA is NOT
- NOT a hosted browser service
- NOT OpenAI Operator ($200/month ChatGPT Pro)
- NOT magically controlling a remote browser
- NOT available via Chat Completions API

## 2. Responses API Implementation

### Install Dependencies
```bash
pip install openai playwright  # Both required!
```

### Core Implementation
```python
from openai import OpenAI
from playwright.async_api import async_playwright
import base64
import os

class OpenAICUABrowser:
    """CUA + YOUR Playwright browser for YC Matcher"""
    
    def __init__(self):
        self.client = OpenAI()
        self.playwright = None
        self.browser = None
        self.page = None
    
    async def start(self):
        """Start YOUR browser that CUA will guide"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=os.getenv("HEADLESS", "1") == "1"
        )
        self.page = await self.browser.new_page()
        await self.page.set_viewport_size({"width": 1024, "height": 768})
    
    async def browse_profiles(self, base_url: str, criteria: dict) -> list:
        """Main workflow using CUA + YOUR browser"""
        profiles = []
        
        # Navigate YOUR browser
        await self.page.goto(base_url)
        
        # CUA loop for browsing
        response = await self._cua_loop(
            "Find and click on the first cofounder profile in the list"
        )
        
        for i in range(criteria.get('max_profiles', 10)):
            # Check STOP flag
            if self._should_stop():
                break
            
            # Extract profile using CUA
            profile_data = await self._extract_profile()
            profiles.append(profile_data)
            
            # Local decision engine
            decision = await self._evaluate(profile_data, criteria)
            
            if decision['should_message']:
                # Use CUA to send message
                sent = await self._send_message(decision['message'])
                profile_data['sent'] = sent
            
            # Use CUA to go back
            await self._cua_loop("Go back to the profile list")
            
            # Use CUA to click next profile
            if i < criteria.get('max_profiles', 10) - 1:
                await self._cua_loop(f"Click on profile number {i+2} in the list")
        
        return profiles
    
    async def _cua_loop(self, goal: str) -> dict:
        """Core CUA loop - YOU execute, CUA guides"""
        
        # Initial request
        response = self.client.responses.create(
            model="computer-use-preview",
            tools=[{
                "type": "computer_use_preview",
                "display_width": 1024,
                "display_height": 768,
                "environment": "browser"
            }],
            input=[{
                "role": "user",
                "content": [{
                    "type": "input_text",
                    "text": goal
                }]
            }],
            truncation="auto"  # REQUIRED
        )
        
        # Loop until no more actions
        while True:
            # Check for computer_call
            computer_calls = [
                item for item in response.output 
                if item.type == "computer_call"
            ]
            
            if not computer_calls:
                return response  # Done!
            
            call = computer_calls[0]
            action = call.action
            
            # Check for safety warnings
            if call.pending_safety_checks:
                # STOP for human review
                if not await self._handle_safety_check(call):
                    return response
            
            # YOU execute the action in YOUR browser
            await self._execute_action(action)
            
            # YOU take screenshot of YOUR browser
            screenshot = await self.page.screenshot()
            screenshot_b64 = base64.b64encode(screenshot).decode()
            
            # Send screenshot back to CUA
            response = self.client.responses.create(
                model="computer-use-preview",
                previous_response_id=response.id,  # Chain conversation
                tools=[{
                    "type": "computer_use_preview",
                    "display_width": 1024,
                    "display_height": 768,
                    "environment": "browser"
                }],
                input=[{
                    "call_id": call.call_id,
                    "type": "computer_call_output",
                    "output": {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{screenshot_b64}"
                    },
                    "current_url": self.page.url  # Help safety checks
                }],
                truncation="auto"
            )
    
    async def _execute_action(self, action):
        """Execute CUA's suggested action in YOUR browser"""
        action_type = action.type
        
        if action_type == "click":
            await self.page.mouse.click(action.x, action.y, button=action.button)
            
        elif action_type == "type":
            await self.page.keyboard.type(action.text)
            
        elif action_type == "scroll":
            await self.page.evaluate(
                f"window.scrollBy({action.scroll_x}, {action.scroll_y})"
            )
            
        elif action_type == "keypress":
            for key in action.keys:
                if key.lower() == "enter":
                    await self.page.keyboard.press("Enter")
                elif key.lower() == "space":
                    await self.page.keyboard.press(" ")
                else:
                    await self.page.keyboard.press(key)
        
        elif action_type == "wait":
            await asyncio.sleep(2)
        
        elif action_type == "screenshot":
            pass  # We take screenshots every loop anyway
    
    async def _extract_profile(self) -> dict:
        """Use CUA to extract profile data"""
        response = await self._cua_loop(
            "Extract the name, skills, location, and bio from the current profile page"
        )
        
        # Parse the text from response
        text = ""
        for item in response.output:
            if hasattr(item, 'text'):
                text += item.text
        
        return {
            "raw_text": text,
            "url": self.page.url
        }
    
    async def _send_message(self, message_text: str) -> bool:
        """Use CUA to send a message"""
        response = await self._cua_loop(
            f"Click the message/connect button, type this message, then send it: {message_text}"
        )
        
        # Verify sent
        verify_response = await self._cua_loop(
            "Check if the message was sent successfully. Look for confirmation text or cleared input."
        )
        
        # Parse response for success indicators
        for item in verify_response.output:
            if hasattr(item, 'text') and 'success' in item.text.lower():
                return True
        
        return False
    
    async def _handle_safety_check(self, call) -> bool:
        """Handle CUA safety warnings - require human approval"""
        safety_check = call.pending_safety_checks[0]
        
        print(f"⚠️ SAFETY CHECK: {safety_check.message}")
        print(f"Code: {safety_check.code}")
        
        # In production, show in UI and wait for user
        # For now, we'll be conservative and stop
        return False  # Don't proceed without approval
    
    async def _evaluate(self, profile: dict, criteria: dict) -> dict:
        """Local decision engine (not CUA)"""
        mode = os.getenv("DECISION_MODE", "advisor")
        
        # This uses regular OpenAI API, not CUA
        if mode == "advisor":
            return await self._advisor_evaluate(profile, criteria)
        elif mode == "rubric":
            return self._rubric_evaluate(profile, criteria)
        elif mode == "hybrid":
            advisor = await self._advisor_evaluate(profile, criteria)
            rubric = self._rubric_evaluate(profile, criteria)
            alpha = float(os.getenv("ALPHA", "0.5"))
            final_score = alpha * advisor['score'] + (1-alpha) * rubric['score']
            return {
                'should_message': final_score >= float(os.getenv("THRESHOLD", "0.72")),
                'message': self._render_message(profile),
                'score': final_score
            }
    
    def _should_stop(self) -> bool:
        """Check STOP flag"""
        return os.path.exists(".runs/stop.flag")
    
    async def cleanup(self):
        """Clean up YOUR browser"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
```

## 3. Headless Browser Setup (For YOUR Playwright)

If running headless on Linux, YOU may need Xvfb:

```bash
# Install Xvfb for headless display
sudo apt-get install xvfb

# Run with virtual display
Xvfb :99 -screen 0 1280x800x24 &
export DISPLAY=:99
```

Or just use Playwright's built-in headless mode:
```python
browser = await playwright.chromium.launch(headless=True)
```

## 4. Integration with Existing Code

### Port Implementation
```python
# application/ports.py
from typing import Protocol

class BrowserPort(Protocol):
    """Port for browser automation"""
    
    async def start(self) -> None: ...
    async def browse_profiles(self, url: str, criteria: dict) -> list: ...
    async def cleanup(self) -> None: ...
```

### Dependency Injection
```python
# interface/di.py
def build_browser():
    if os.getenv("ENABLE_CUA") == "1":
        from infrastructure.openai_cua_browser import OpenAICUABrowser
        return OpenAICUABrowser()  # CUA + Playwright
    elif os.getenv("ENABLE_PLAYWRIGHT_FALLBACK") == "1":
        from infrastructure.browser_playwright import PlaywrightBrowser
        return PlaywrightBrowser()  # Playwright only (no CUA)
    else:
        raise ValueError("No browser adapter configured")
```

## 5. Testing Strategy

### Unit Tests (Mock Everything)
```python
@pytest.fixture
def mock_openai_client():
    """Mock the OpenAI client"""
    client = Mock()
    client.responses.create.return_value = Mock(
        output=[],
        id="test_response_id"
    )
    return client
```

### Integration Tests (Real Playwright, Mock CUA)
```python
@pytest.mark.asyncio
async def test_cua_browser_integration():
    """Test CUA browser with real Playwright, mocked API"""
    browser = OpenAICUABrowser()
    browser.client = mock_openai_client()
    
    await browser.start()
    try:
        # Test against local HTML fixture
        profiles = await browser.browse_profiles(
            "file:///path/to/fixture.html",
            {"max_profiles": 1}
        )
        assert len(profiles) == 1
    finally:
        await browser.cleanup()
```

## 6. Configuration Reference

```bash
# CUA Configuration
ENABLE_CUA=1
CUA_MODEL=computer-use-preview      # From your Models endpoint
OPENAI_API_KEY=sk-...

# Decision Engine (separate from CUA)
OPENAI_DECISION_MODEL=gpt-4-turbo   # Regular OpenAI model
DECISION_MODE=advisor|rubric|hybrid
THRESHOLD=0.72
ALPHA=0.50

# Safety & Limits
DAILY_QUOTA=25
WEEKLY_QUOTA=120
PACE_MIN_SECONDS=45

# Browser Settings (for YOUR Playwright)
HEADLESS=1                           # Your browser visibility
PLAYWRIGHT_BROWSERS_PATH=.ms-playwright

# YC Config
YC_MATCH_URL=https://www.startupschool.org/cofounder-matching
```

## 7. Common Pitfalls

### ❌ WRONG: Expecting Hosted Browser
```python
# WRONG - CUA doesn't provide a browser
agent = Agent(tools=[ComputerTool()])
result = agent.browse("https://example.com")  # This doesn't exist!
```

### ✅ RIGHT: YOU Provide Browser
```python
# RIGHT - YOU control the browser
playwright = await async_playwright().start()
browser = await playwright.chromium.launch()
page = await browser.new_page()

# CUA analyzes YOUR screenshots
screenshot = await page.screenshot()
# Send to CUA for analysis...
```

### ❌ WRONG: Using Chat Completions
```python
# WRONG - Computer Use is NOT on Chat Completions
response = client.chat.completions.create(
    model="computer-use-preview",  # This won't work!
    ...
)
```

### ✅ RIGHT: Using Responses API
```python
# RIGHT - Use Responses API
response = client.responses.create(
    model="computer-use-preview",
    tools=[{"type": "computer_use_preview", ...}],
    truncation="auto"  # Required!
)
```

## 8. Troubleshooting

### "Model not available"
- Check your Models endpoint
- Verify you have access to `computer-use-preview`
- Confirm API key permissions

### "Computer action failed"
- Check YOUR Playwright browser is running
- Verify screenshot is being captured
- Check action coordinates are within viewport

### "High token usage"
- Reduce screenshot frequency
- Batch related actions
- Use concise prompts

### "Truncation error"
- MUST set `truncation="auto"` for computer use
- This is required, not optional

## Resources
- [Computer Use Guide](https://platform.openai.com/docs/guides/tools-computer-use)
- [Responses API](https://platform.openai.com/docs/guides/responses)
- [Playwright Docs](https://playwright.dev/python/)
- [Models Endpoint](https://platform.openai.com/account/models)
