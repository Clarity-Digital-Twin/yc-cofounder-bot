# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YC Co-Founder Matching Bot - Autonomous browser automation for YC/Startup School cofounder matching using Playwright + GPT-4.

The system takes 3 inputs (Your Profile, Match Criteria, Message Template) and autonomously browses YC Cofounder Matching, evaluates profiles using GPT-4, and sends messages when match quality exceeds threshold.

## Quick Status (September 2025)

✅ **Working**: Playwright browser automation, GPT-4 evaluation, message sending
⚙️ **Needs Config**: Set YC_EMAIL, YC_PASSWORD, and OPENAI_API_KEY in .env
📋 **Fixed**: Removed unsupported `response_format` parameter for GPT-4

## Essential Commands

```bash
# Setup
make setup          # Install deps + browsers
make browsers       # Install Playwright locally

# Development
make lint           # Run ruff lints
make type           # Run mypy type checking
make verify         # Lint + type + tests

# Run the Bot
make run            # Launch Streamlit UI
PYTHONPATH=src make run  # If import errors

# Testing
make test           # Run unit tests
```

## Architecture (Domain-Driven Design)

```
src/yc_matcher/
├── domain/          # Pure business logic (no external deps)
│   ├── ports/       # Interfaces/contracts
│   └── models/      # Domain entities
├── application/     # Use cases (orchestration)
├── infrastructure/  # External implementations
│   ├── ai/         # OpenAI adapters
│   ├── browser/    # Playwright automation
│   └── persistence/# SQLite repositories
└── interface/       # Entry points
    └── web/        # Streamlit UI
```

## Key Configuration (.env)

```bash
# Required
OPENAI_API_KEY=sk-...
YC_EMAIL=your-email@example.com
YC_PASSWORD=your-password

# Model & Decision
OPENAI_DECISION_MODEL=gpt-4o  # or gpt-4-turbo
DECISION_MODE=ai               # ai/rubric/hybrid
THRESHOLD=0.72                 # Auto-send threshold

# Safety
DAILY_QUOTA=25
WEEKLY_QUOTA=120
PACE_MIN_SECONDS=45
SHADOW_MODE=0                  # 1 = test only, no sends
```

## Decision Modes

1. **AI Mode** (`ai`): GPT-4 evaluates profiles
2. **Rubric Mode** (`rubric`): Keyword-based scoring
3. **Hybrid Mode** (`hybrid`): Combines both approaches

## Safety Mechanisms

- **STOP Flag**: `.runs/stop.flag` halts immediately
- **Quotas**: Daily/weekly limits enforced
- **Deduplication**: Never message same profile twice
- **Pacing**: Minimum 45 seconds between sends
- **Shadow Mode**: Test without actually sending

## Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "No module named 'yc_matcher'" | Use `PYTHONPATH=src` prefix |
| "Browser not launching" | Run `make browsers` |
| "response_format not supported" | Already fixed in code |
| "Model not found" | Check OPENAI_DECISION_MODEL in .env |

## Implementation Notes

### Working Implementation Pattern
```python
# GPT-4 Decision (openai_decision.py)
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    temperature=0.3,
    max_tokens=800
    # NO response_format parameter for GPT-4
)
```

### Browser Automation Flow
1. Playwright navigates to YC
2. Auto-login with credentials
3. Browse profiles (detects `/candidate/` URLs)
4. Extract profile text
5. Send to GPT-4 for evaluation
6. Send message if score > threshold

## Testing the Bot

```bash
# 1. Test browser automation
PYTHONPATH=src python -c "
from yc_matcher.infrastructure.browser.browser_playwright import test_browser
test_browser()
"

# 2. Test AI evaluation
PYTHONPATH=src python -c "
from yc_matcher.infrastructure.ai.openai_decision import test_decision
test_decision()
"

# 3. Run full pipeline
make run
# Then use Streamlit UI
```

## Clean Code Principles

- **SOLID**: Single responsibility, dependency injection
- **DDD**: Domain logic pure, infrastructure swappable
- **Type Safety**: Full type hints required
- **Testing**: Write tests first (TDD)

## Documentation

- Main docs: `/docs/README.md`
- Technical status: `/docs/technical/PROJECT_STATUS.md`
- API guide: `/docs/technical/OPENAI_API_GUIDE.md`