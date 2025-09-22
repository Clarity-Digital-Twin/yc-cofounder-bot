# YC Co-Founder Bot - Project Status
*September 2025*

## Quick Start

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your credentials

# 2. Install dependencies
make setup

# 3. Run the bot
make run  # Opens Streamlit UI on localhost:8501
```

## What's Working ✅

### Core Pipeline
- **Playwright Browser Automation**: Navigates YC, takes screenshots
- **GPT-4 Decision Making**: Evaluates profiles against criteria
- **Message Sending**: Automated outreach to matches
- **Safety Controls**: Quotas, deduplication, STOP flag

### Decision Modes
1. **AI Mode** (`DECISION_MODE=ai`): GPT-4 evaluates profiles
2. **Rubric Mode** (`DECISION_MODE=rubric`): Keyword-based scoring
3. **Hybrid Mode** (`DECISION_MODE=hybrid`): Combines both approaches

## What Needs Configuration ⚙️

### Required in .env
```bash
# YC Credentials
YC_EMAIL=your-email@example.com
YC_PASSWORD=your-password

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_DECISION_MODEL=gpt-4o  # or gpt-4-turbo

# Decision Settings
DECISION_MODE=ai
THRESHOLD=0.72  # Auto-send if score > threshold
```

## Known Issues & Fixes

### Issue 1: Module Import Errors
**Fix**: Always run with `PYTHONPATH=src`
```bash
PYTHONPATH=src python src/yc_matcher/interface/web/ui_streamlit.py
```

### Issue 2: GPT-4 Response Format Error
**Status**: ✅ FIXED - Removed unsupported `response_format` parameter

### Issue 3: Playwright Browser Not Found
**Fix**: Install browsers locally
```bash
make browsers
```

## Project Structure

```
src/yc_matcher/
├── domain/          # Business logic & interfaces
├── application/     # Use cases & orchestration
├── infrastructure/  # External implementations
│   ├── ai/         # OpenAI adapters
│   ├── browser/    # Playwright automation
│   └── persistence/# SQLite repositories
└── interface/      # Entry points
    └── web/        # Streamlit UI
```

## Testing the Bot

### 1. Test Browser Automation
```bash
PYTHONPATH=src python -c "
from yc_matcher.infrastructure.browser.browser_playwright import test_browser
test_browser()
"
```

### 2. Test AI Decision Making
```bash
PYTHONPATH=src python -c "
from yc_matcher.infrastructure.ai.openai_decision import test_decision
test_decision()
"
```

### 3. Run Full Pipeline
```bash
make run
# Then in UI:
# 1. Paste your profile
# 2. Set criteria
# 3. Configure message template
# 4. Click "Start Matching"
```

## Safety Features

- **STOP Flag**: Create `.runs/stop.flag` to halt immediately
- **Daily Quota**: Default 25 messages/day
- **Weekly Quota**: Default 120 messages/week
- **Deduplication**: Never message same profile twice
- **Pacing**: 45+ seconds between messages

## Monitoring

Check `.runs/events.jsonl` for:
- Decision events with scores and rationale
- Send confirmations
- Error messages
- Token usage and costs