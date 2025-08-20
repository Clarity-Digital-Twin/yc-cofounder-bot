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
        
    async def _ensure_browser(self):
        """Ensure Playwright browser is running"""
        if not self.playwright:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch()
            self.page = await self.browser.new_page()
        
    async def _cua_action(self, instruction: str):
        """Core loop: Playwright executes, CUA analyzes"""
        await self._ensure_browser()
        
        # Playwright takes screenshot
        screenshot = await self.page.screenshot()
        screenshot_b64 = base64.b64encode(screenshot).decode()
        
        # CUA analyzes YOUR screenshot
        response = self.client.responses.create(
            model=self.model,
            messages=[{"role": "user", "content": instruction}],
            tools=[{
                "type": "computer_use_preview",
                "display": {
                    "screenshot": screenshot_b64,
                    "width": 1920,
                    "height": 1080
                }
            }],
            truncation="auto"  # REQUIRED!
        )
        
        # YOU execute CUA's suggestion
        if response.tool_calls:
            action = response.tool_calls[0]
            await self._execute_action(action)
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