# OpenAI Computer Use - THE ACTUAL TRUTH

## Package and Import Facts

### CORRECT Information:
- **Package name**: `openai-agents` (install via `pip install openai-agents`)
- **Import statement**: `from agents import Agent, ComputerTool, Session`
- **NOT** `from openai_agents import ...` (this is WRONG)
- **Version**: 0.2.8 (as of Aug 2025)

### How It Actually Works:

```python
# CORRECT imports
from agents import Agent, ComputerTool, Session
import os

# Initialize agent with Computer Use
agent = Agent(
    model=os.getenv("CUA_MODEL"),  # ALWAYS from env, never hardcoded
    tools=[ComputerTool()],
    temperature=0.3
)

# Run actions
result = agent.run(
    messages=[{"role": "user", "content": "Navigate to example.com"}],
    tools=[ComputerTool()],
    session=Session()
)
```

## Environment Setup

### Required Dependencies:
```bash
pip install openai-agents  # The agents SDK
pip install openai          # Base OpenAI SDK
```

### Environment Variables:
```bash
OPENAI_API_KEY=sk-...                    # Your OpenAI API key
CUA_MODEL=<your account's computer-use model>    # From Models endpoint
ENABLE_CUA=1                             # Enable Computer Use
ENABLE_PLAYWRIGHT_FALLBACK=1             # Fallback option
```

## Access Requirements:
- **Tier 3-5 OpenAI account** required for Computer Use
- Check available models at: https://platform.openai.com/account/models
- Computer Use documentation: https://platform.openai.com/docs/guides/tools-computer-use

## Common Mistakes to Avoid:

### ❌ WRONG:
```python
from openai_agents import ComputerTool  # WRONG - module not named this
from openai import ComputerTool         # WRONG - not in base SDK
import openai.agents                    # WRONG - doesn't exist
```

### ✅ CORRECT:
```python
from agents import Agent, ComputerTool, Session  # RIGHT!
```

## File Locations in This Project:

### Implementation:
- `/src/yc_matcher/infrastructure/openai_cua_browser.py` - CUA adapter

### Documentation:
- `/docs/vendor/openai/OPENAI_CUA_GUIDE.md` - Usage guide
- `/docs/vendor/openai/OPENAI_CUA_TECHNICAL_GUIDE.md` - Technical details

### Configuration:
- `.env` - Set OPENAI_API_KEY and CUA_MODEL
- `/src/yc_matcher/interface/di.py` - Dependency injection setup

## Testing Computer Use:

Run this command to verify setup:
```bash
make check-cua
# Or directly:
uv run python -m yc_matcher.interface.cli.check_cua
```

## The Computer Use Flow:

1. **CUA takes screenshot** of current browser/screen
2. **Analyzes** what it sees
3. **Decides** on action (click, type, scroll)
4. **Executes** the action
5. **Verifies** success
6. **Repeats** until task complete

## Pricing:
- **Input**: $3 per 1M tokens
- **Output**: $12 per 1M tokens
- Typical session: ~$0.50 for 20 profiles

## Important Notes:

1. **This is OpenAI's Computer Use**, not Anthropic's
2. The package is `openai-agents` but imports as `agents`
3. Requires tier 3-5 access on OpenAI
4. Currently in research preview
5. Use Playwright as fallback when CUA unavailable

## Quick Test:

```python
# Test if imports work
from agents import Agent, ComputerTool, Session
print("✅ Imports successful!")

# Test initialization
agent = Agent(model=os.getenv("CUA_MODEL"), tools=[ComputerTool()])
print("✅ Agent created!")
```

---
Last verified: August 2025
Package version: openai-agents==0.2.8