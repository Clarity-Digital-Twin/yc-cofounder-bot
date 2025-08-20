# OpenAI Computer Use Guide

## Overview
OpenAI's Computer Use tool (via the Responses API) enables AI to control computer interfaces by analyzing screenshots and suggesting actions. **YOU provide the browser environment** (via Playwright), execute the actions, and send screenshots back to the model in a loop.

## Availability
- **Access**: Beta preview - check your account's Models endpoint
- **API**: Responses API with `computer-use-preview` model
- **Tool**: `computer_use_preview` tool type
- **Requirements**: YOU must provide the browser/VM environment

## Pricing
- Billed at model token rates
- Some tools may have additional per-call charges
- **Do not hardcode prices** - consult [OpenAI Pricing](https://openai.com/api/pricing/)
- Monitor actual usage via your account dashboard

## How It ACTUALLY Works

### Core Architecture
1. **YOU provide a browser** (Playwright, Selenium, etc.)
2. **YOU take screenshots** of YOUR browser
3. **CUA analyzes** the screenshots and suggests actions
4. **YOU execute** the actions in YOUR browser
5. **YOU capture** the updated state and send it back
6. **Repeat** until task complete

### The Loop
```
Your Browser (Playwright) → Screenshot → CUA Analysis → Action Suggestion
         ↑                                                      ↓
         ←─────────── You Execute Action ←─────────────────────
```

## Implementation

### 1. Install Dependencies
```bash
pip install openai playwright  # YOU need Playwright for browser control
```

### 2. Set Up YOUR Browser Environment
```python
from playwright.async_api import async_playwright
from openai import OpenAI
import base64

# YOU provide the browser
playwright = await async_playwright().start()
browser = await playwright.chromium.launch()
page = await browser.new_page()

# Navigate to YOUR target site
await page.goto("https://www.startupschool.org/cofounder-matching")
```

### 3. The CUA Loop
```python
client = OpenAI()

# Initial request with YOUR goal
response = client.responses.create(
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
            "text": "Navigate to profile list and extract first profile"
        }]
    }],
    truncation="auto"  # REQUIRED for computer use
)

# Loop until no more actions
while True:
    # Check for computer_call in response
    computer_calls = [item for item in response.output 
                     if item.type == "computer_call"]
    
    if not computer_calls:
        break  # Done!
    
    action = computer_calls[0].action
    call_id = computer_calls[0].call_id
    
    # YOU execute the action in YOUR browser
    if action.type == "click":
        await page.mouse.click(action.x, action.y)
    elif action.type == "type":
        await page.keyboard.type(action.text)
    elif action.type == "scroll":
        await page.evaluate(f"window.scrollBy({action.scroll_x}, {action.scroll_y})")
    
    # YOU take a screenshot of YOUR browser
    screenshot_bytes = await page.screenshot()
    screenshot_base64 = base64.b64encode(screenshot_bytes).decode()
    
    # Send the screenshot back to CUA
    response = client.responses.create(
        model="computer-use-preview",
        previous_response_id=response.id,  # Chain the conversation
        tools=[{
            "type": "computer_use_preview",
            "display_width": 1024,
            "display_height": 768,
            "environment": "browser"
        }],
        input=[{
            "call_id": call_id,
            "type": "computer_call_output",
            "output": {
                "type": "input_image",
                "image_url": f"data:image/png;base64,{screenshot_base64}"
            }
        }],
        truncation="auto"
    )
```

## YC Matcher Integration

### OpenAICUABrowser Implementation
```python
from openai import OpenAI
from playwright.async_api import async_playwright
import base64
import os

class OpenAICUABrowser:
    """Browser automation via CUA + YOUR Playwright browser."""
    
    def __init__(self):
        self.client = OpenAI()
        self.browser = None
        self.page = None
    
    async def start(self):
        """Start YOUR browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=os.getenv("HEADLESS", "1") == "1"
        )
        self.page = await self.browser.new_page()
    
    async def browse_to_profile(self, url: str) -> dict:
        """Navigate and extract using CUA + YOUR browser"""
        # Navigate YOUR browser
        await self.page.goto(url)
        
        # Start CUA analysis loop
        response = await self._cua_loop(
            "Extract all profile information from this page"
        )
        
        return self._parse_response(response)
    
    async def send_message(self, message: str) -> bool:
        """Fill and send using CUA + YOUR browser"""
        response = await self._cua_loop(
            f"Click the message box, type this message, then click send: {message}"
        )
        
        # Verify in YOUR browser
        return await self._verify_sent()
    
    async def _cua_loop(self, goal: str):
        """The core CUA loop with YOUR browser"""
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
                "content": [{"type": "input_text", "text": goal}]
            }],
            truncation="auto"
        )
        
        while True:
            computer_calls = [item for item in response.output 
                            if item.type == "computer_call"]
            
            if not computer_calls:
                return response
            
            # Execute in YOUR browser
            await self._execute_action(computer_calls[0].action)
            
            # Screenshot YOUR browser
            screenshot = await self.page.screenshot()
            screenshot_b64 = base64.b64encode(screenshot).decode()
            
            # Continue loop
            response = self.client.responses.create(
                model="computer-use-preview",
                previous_response_id=response.id,
                tools=[{
                    "type": "computer_use_preview",
                    "display_width": 1024,
                    "display_height": 768,
                    "environment": "browser"
                }],
                input=[{
                    "call_id": computer_calls[0].call_id,
                    "type": "computer_call_output",
                    "output": {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{screenshot_b64}"
                    }
                }],
                truncation="auto"
            )
    
    async def _execute_action(self, action):
        """Execute CUA action in YOUR browser"""
        if action.type == "click":
            await self.page.mouse.click(action.x, action.y)
        elif action.type == "type":
            await self.page.keyboard.type(action.text)
        elif action.type == "scroll":
            await self.page.evaluate(
                f"window.scrollBy({action.scroll_x}, {action.scroll_y})"
            )
        # Add other action types as needed
```

## Configuration

### Environment Variables
```bash
# Core Settings
ENABLE_CUA=1
CUA_MODEL=computer-use-preview          # From your Models endpoint
OPENAI_API_KEY=sk-...

# Decision Engine (separate from CUA)
OPENAI_DECISION_MODEL=<your-best-llm>   # For Advisor/Hybrid
DECISION_MODE=advisor|rubric|hybrid

# Safety & Limits
DAILY_QUOTA=25
WEEKLY_QUOTA=120
SEND_DELAY_MS=5000
THRESHOLD=0.72

# Browser Settings (for YOUR Playwright)
HEADLESS=1                               # 0 for visible browser
```

## Safety Implementation

### Handling Safety Checks
```python
# If pending_safety_checks in response
if any(item.pending_safety_checks for item in response.output):
    # STOP and require human approval
    safety_check = response.output[0].pending_safety_checks[0]
    
    # Show to user and wait for approval
    if user_approves:
        # Continue with acknowledgment
        response = client.responses.create(
            model="computer-use-preview",
            previous_response_id=response.id,
            input=[{
                "type": "computer_call_output",
                "call_id": call_id,
                "acknowledged_safety_checks": [safety_check],
                "output": {"type": "input_image", "image_url": screenshot}
            }],
            truncation="auto"
        )
```

## Critical Points

1. **YOU provide the browser** - CUA does NOT have a hosted browser
2. **YOU execute actions** - CUA only suggests what to do
3. **YOU take screenshots** - and send them to CUA for analysis
4. **Responses API only** - NOT Chat Completions, NOT Agents SDK Runner
5. **truncation="auto"** is REQUIRED for computer use
6. **previous_response_id** chains the conversation
7. **Safety checks** require human approval

## Resources
- [Computer Use Guide](https://platform.openai.com/docs/guides/tools-computer-use)
- [Responses API](https://platform.openai.com/docs/guides/responses)
- [Models Endpoint](https://platform.openai.com/account/models)
- [API Pricing](https://openai.com/api/pricing/)