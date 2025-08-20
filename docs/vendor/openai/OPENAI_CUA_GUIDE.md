# OpenAI Computer-Using Agent (CUA) Guide

## Overview
OpenAI's Computer-Using Agent (CUA) was released in March 2025 as part of the Responses API. It enables AI agents to interact with computer interfaces through screenshots and actions.

## Availability
- **Access**: Available for developers in usage tiers 3-5
- **Status**: Research preview
- **API**: Accessible via the Responses API

## Pricing
- **Input**: $3 per 1M tokens
- **Output**: $12 per 1M tokens
- Billed at the chosen language model's rates (not separately priced)

## How It Works

### Core Flow
1. CUA takes a screenshot of the computer interface
2. Analyzes the visual elements
3. Recommends actions via `computer_call(s)`
4. Your code executes the actions
5. Sends back new screenshots for next steps

### Available Actions
- `click(x, y)` - Click at specific coordinates
- `type(text)` - Type text input
- Navigation actions (scroll, etc.)

## Implementation

### Using the Responses API
```python
# Example structure (conceptual)
import openai

client = openai.Client(api_key="sk-...")

response = client.responses.create(
    model="computer-use-preview",
    messages=[
        {"role": "system", "content": "Navigate to YC cofounder matching"},
        {"role": "user", "content": [screenshot_data]}
    ],
    tools=["computer_use"]
)

# Response contains computer_call actions
for action in response.computer_calls:
    if action.type == "click":
        execute_click(action.x, action.y)
    elif action.type == "type":
        execute_type(action.text)
```

## Capabilities
- **Autonomous UI navigation**: Opens applications, clicks buttons, fills forms
- **Dynamic adaptation**: Interprets UI changes and adjusts actions
- **Cross-application**: Works across web and desktop apps
- **No API dependencies**: Operates through visual interface

## Performance
- **OSWorld Benchmark**: 38.1% accuracy
- **Recommendation**: Human oversight required for critical tasks
- **Best for**: Research, prototyping, semi-automated workflows

## Integration Points

### For YC Cofounder Bot
1. **Profile Discovery**: CUA navigates YC list
2. **Profile Reading**: Screenshots and extracts text
3. **Message Sending**: Fills forms and clicks send
4. **Verification**: Confirms action success

### Safety Considerations
- Implement quotas and rate limiting
- Add STOP flag checks before actions
- Log all actions for audit trail
- Verify critical actions succeeded

## Sample App
OpenAI provides a sample app: https://github.com/openai/openai-cua-sample-app

## Key Differences from Competitors
- **vs Anthropic Claude**: OpenAI uses Responses API, not Messages API
- **Pricing**: OpenAI is cheaper ($3/1M vs Anthropic's higher rates)
- **Availability**: Tier 3-5 developers only

## Environment Variables for Our App
```bash
ENABLE_CUA=1
OPENAI_API_KEY=sk-...
# No CUA_PROVIDER needed - OpenAI only
```

## Important Notes
- Research preview - expect changes
- Not production-ready for high-stakes tasks
- Requires screenshot capability in your environment
- Best with 1280x800 or similar resolution