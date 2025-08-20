# Section 1: CUA Browser Implementation

## Current File: `src/yc_matcher/infrastructure/openai_cua_browser.py`

### What EXISTS Now:
- **Lines**: ~200 lines
- **Uses**: OpenAI Agents SDK (`from agents import Agent, ComputerTool, Session`)
- **Model**: Gets from `CUA_MODEL` env var ✅ GOOD
- **Temperature**: Configurable via `CUA_TEMPERATURE` ✅ GOOD
- **Methods Implemented**:
  - `open(url)` - Navigate to URL
  - `click_view_profile()` - Click profile button
  - `read_profile_text()` - Extract profile text
  - `focus_message_box()` - Focus on message input
  - `fill_message(text)` - Type message
  - `send()` - Send message
  - `skip()` - Skip profile
  - `verify_sent()` - Verify message sent

### What's WRONG:
1. **WRONG API**: Uses Agents SDK instead of Responses API
2. **MISSING PLAYWRIGHT**: CUA can't work alone - needs Playwright to execute actions!
3. **No Screenshot Loop**: Doesn't show Playwright→screenshot→CUA→action loop
4. **Missing Methods**: No autonomous browsing capabilities

### How to FIX:

```python
# CHANGE FROM (current):
from agents import Agent, ComputerTool, Session
self.agent = Agent(model=self.model, tools=[ComputerTool()])
result = self.agent.run(messages=[...], tools=[ComputerTool()])

# CHANGE TO (correct):
from openai import OpenAI
import base64

class OpenAICUABrowser:
    def __init__(self):
        self.client = OpenAI()
        self.model = os.getenv("CUA_MODEL")
        # CRITICAL: CUA needs Playwright to execute!
        self.playwright = None
        self.browser = None
        self.page = None
        self.prev_id = None
        
    async def _ensure_browser(self):
        """Ensure Playwright browser is running"""
        if not self.playwright:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch()
            self.page = await self.browser.new_page()
        
    async def _cua_action(self, instruction: str):
        """Core loop: CUA plans; Playwright executes; send computer_call_output each turn"""
        await self._ensure_browser()
        
        # Start or continue a CUA planning turn
        response = self.client.responses.create(
            model=self.model,
            input=[{"role": "user", "content": instruction}],
            tools=[{"type": "computer_use_preview", "display_width": 1920, "display_height": 1080}],
            truncation="auto",
            previous_response_id=self.prev_id,
        )
        
        # If model requests a computer_call, execute via Playwright, screenshot, then send output
        if getattr(response, "computer_call", None):
            action = response.computer_call
            await self._execute_action(action)
            screenshot = await self.page.screenshot()
            screenshot_b64 = base64.b64encode(screenshot).decode()
            follow = self.client.responses.create(
                model=self.model,
                previous_response_id=response.id,
                computer_call_output={
                    "call_id": action.id,
                    "screenshot": screenshot_b64,
                },
                truncation="auto",
            )
            self.prev_id = follow.id
```

### Test Coverage:
- **Current**: 0 tests ❌
- **Needed**: `tests/unit/test_openai_cua_browser.py`

### Environment Variables:
- `CUA_MODEL` - ✅ Already used
- `CUA_TEMPERATURE` - ✅ Already used
- `ENABLE_CUA` - ✅ Used in DI layer

### Effort Estimate:
- **Lines to change**: ~150 out of 200
- **Time**: 2-3 hours
- **Risk**: Medium (core functionality change)
- **Testing**: Add 10-15 unit tests
