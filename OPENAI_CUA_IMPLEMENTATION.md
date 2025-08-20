# OpenAI Computer Use - Implementation Guide

## Critical Understanding

**YOU provide the browser via Playwright. OpenAI CUA only analyzes screenshots and suggests actions.**

## How It Actually Works

### The Responses API Approach

```python
from openai import OpenAI
import base64

client = OpenAI()

# YOU control the browser
playwright = await async_playwright().start()
browser = await playwright.chromium.launch()
page = await browser.new_page()

# YOU take screenshot
screenshot = await page.screenshot()
screenshot_base64 = base64.b64encode(screenshot).decode()

# CUA analyzes YOUR screenshot
response = client.responses.create(
    model=os.getenv("CUA_MODEL"),  # From env, never hardcoded
    messages=[
        {
            "role": "user",
            "content": f"Navigate to YC cofounder listing and find profiles matching: {criteria}"
        }
    ],
    tools=[{
        "type": "computer_use_preview",
        "display": {
            "screenshot": screenshot_base64,
            "width": 1920,
            "height": 1080
        }
    }],
    truncation="auto"  # REQUIRED for Computer Use
)

# CUA suggests action, YOU execute it
if response.tool_calls:
    action = response.tool_calls[0]
    # YOU execute in YOUR browser
    if action.type == "click":
        await page.click(action.coordinates)
    elif action.type == "type":
        await page.type(action.selector, action.text)
```

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...                          # Your API key
CUA_MODEL=<your-computer-use-model>           # From your Models endpoint
OPENAI_DECISION_MODEL=<your-best-model>       # For decision making

# Feature Flags (for refactoring)
USE_CUA_PRIMARY=false                         # Enable CUA as primary
USE_THREE_INPUT_UI=false                      # Enable new UI
USE_DECISION_MODES=false                      # Enable decision modes
DEFAULT_DECISION_MODE=rubric                  # advisor|rubric|hybrid

# Pacing
SEND_DELAY_MS=5000                           # Delay between messages
```

## Implementation in This Project

### Current State (WRONG)
- Paste-based UI expecting manual input
- CUA only used for message sending
- Missing decision modes

### Target State (FROM DOCS)
- 3-input UI (Your Profile, Criteria, Template)
- CUA drives entire browsing flow
- Three decision modes (Advisor, Rubric, Hybrid)

### Files to Change
```
src/yc_matcher/
├── infrastructure/
│   └── openai_cua_browser.py    # Needs to use Responses API
├── application/
│   ├── use_cases/
│   │   └── process_autonomous.py # Create new
│   └── decision_modes/           # Create new
│       ├── advisor.py
│       ├── rubric.py
│       └── hybrid.py
└── interface/
    └── web/
        └── ui_streamlit_v2.py    # Create 3-input UI
```

## The CUA Loop

```python
async def cua_browse_and_match(your_profile, criteria, template):
    # 1. YOU launch browser
    page = await launch_browser()
    
    # 2. Loop: screenshot → analyze → action
    while not done:
        # YOU take screenshot
        screenshot = await page.screenshot()
        
        # CUA analyzes
        response = client.responses.create(
            model=os.getenv("CUA_MODEL"),
            messages=messages,
            tools=[computer_use_tool(screenshot)],
            truncation="auto"
        )
        
        # YOU execute suggested action
        await execute_action(page, response.tool_calls[0])
        
        # Continue until profiles processed
```

## Decision Modes

### Advisor Mode (LLM-only, no auto-send)
```python
decision = await llm.evaluate(profile, your_profile, criteria)
# Never auto-sends, user reviews all decisions
```

### Rubric Mode (Deterministic, auto-send)
```python
score = calculate_score(profile, criteria)
if score >= threshold:
    auto_send_message()  # Automatic
```

### Hybrid Mode (Weighted combination)
```python
ai_score = await llm.evaluate(...)
rule_score = calculate_score(...)
combined = (ai_weight * ai_score) + ((1-ai_weight) * rule_score)
if combined >= threshold:
    auto_send_message()
```

## Testing Requirements

### Must Test
1. CUA Responses API integration
2. Three decision modes
3. 3-input UI flow
4. Safety features (STOP, quotas)

### Currently Missing (0% coverage)
- ANY CUA tests
- Decision mode tests
- 3-input UI tests
- Autonomous flow integration tests

## Refactoring Steps

See the 4-part refactoring plan:
1. [REFACTOR_PART_1_FOUNDATION.md](./REFACTOR_PART_1_FOUNDATION.md)
2. [REFACTOR_PART_2_CORE_FLOW.md](./REFACTOR_PART_2_CORE_FLOW.md)
3. [REFACTOR_PART_3_INTERFACE.md](./REFACTOR_PART_3_INTERFACE.md)
4. [REFACTOR_PART_4_VALIDATION.md](./REFACTOR_PART_4_VALIDATION.md)

## Common Pitfalls

❌ **DON'T**: Think CUA provides the browser (it doesn't!)
✅ **DO**: Use Playwright to control browser, CUA to analyze

❌ **DON'T**: Use Agents SDK or Chat Completions API
✅ **DO**: Use Responses API with `truncation="auto"`

❌ **DON'T**: Hardcode model names
✅ **DO**: Always use environment variables

❌ **DON'T**: Skip tests
✅ **DO**: Test CUA integration thoroughly

## Success Criteria

- [ ] CUA via Responses API drives browsing
- [ ] YOU provide browser via Playwright
- [ ] Three decision modes work correctly
- [ ] 3-input UI replaces paste UI
- [ ] All tests pass including CUA tests
- [ ] Feature flags enable safe rollback