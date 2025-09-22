# YC Co-Founder Matching Bot Documentation

## 🚀 Quick Status: 99% Functional

**Last Updated**: December 2025 | **SDK**: v1.108.1 | **Status**: Ready to Run

## What This Is

An autonomous bot that finds co-founders on YC Startup School by:
1. **Browsing** profiles automatically using OpenAI Computer Use or Playwright
2. **Evaluating** profiles with GPT-5/GPT-4 against your criteria
3. **Messaging** high-quality matches automatically (with safeguards)

**3 Key Inputs**: Your Profile → Match Criteria → Message Template → Done!

## ✅ Current Status

### Working Components
- **OpenAI Responses API**: Verified working with SDK v1.108.1
- **GPT-5 Models**: Full access (gpt-5, gpt-5-mini, gpt-5-nano)
- **Computer Use**: Available via computer-use-preview model
- **Playwright Browser**: Tested and functional
- **Decision Evaluation**: All three modes implemented
- **Safety Systems**: Quotas, deduplication, STOP flag

### Recent Fixes
- ✅ Fixed GPT-4 `response_format` incompatibility (line 405)
- ✅ Upgraded SDK to v1.108.1 with Responses API support
- ✅ Installed Playwright browsers locally

## 📁 Documentation Structure

### Core Documentation (`/core`)
- [`01-product-brief.md`](core/01-product-brief.md) - Product vision and decision modes
- [`02-scope-and-requirements.md`](core/02-scope-and-requirements.md) - Functional/non-functional requirements
- [`03-architecture.md`](core/03-architecture.md) - DDD architecture with ports/adapters
- [`04-implementation-plan.md`](core/04-implementation-plan.md) - Development milestones
- [`05-operations-and-safety.md`](core/05-operations-and-safety.md) - Safety mechanisms and quotas
- [`09-roadmap.md`](core/09-roadmap.md) - Future development roadmap
- [`10-ui-reference.md`](core/10-ui-reference.md) - Streamlit UI documentation
- [`12-prompts-and-rubric.md`](core/12-prompts-and-rubric.md) - Decision prompts and scoring

### Technical Documentation (`/technical`)
- [`OPENAI_API_STATUS.md`](technical/OPENAI_API_STATUS.md) - **⭐ CRITICAL: API availability and models**
- [`CURRENT_STATUS.md`](technical/CURRENT_STATUS.md) - **⭐ Current implementation status**
- [`event_schema.md`](technical/event_schema.md) - Event logging schema
- [`YC_UI_STRUCTURE.md`](technical/YC_UI_STRUCTURE.md) - YC website structure

### Development Documentation (`/development`)
- [`06-dev-environment.md`](development/06-dev-environment.md) - Environment setup and configuration
- [`07-project-structure.md`](development/07-project-structure.md) - Codebase organization
- [`08-testing-quality.md`](development/08-testing-quality.md) - Testing approach
- [`11-engineering-guidelines.md`](development/11-engineering-guidelines.md) - Clean code principles
- [`MCP_SETUP.md`](development/MCP_SETUP.md) - Context7 MCP configuration

### Status Reports (Historical Context)
- [`PLAYWRIGHT_BOT_STATUS.md`](PLAYWRIGHT_BOT_STATUS.md) - Playwright-only pipeline status
- [`P0_BLOCKERS_DEFINITIVE.md`](P0_BLOCKERS_DEFINITIVE.md) - Critical issues (all fixed)
- [`FINAL_STATUS_DECEMBER_2025.md`](FINAL_STATUS_DECEMBER_2025.md) - December 2025 status
- [`OPENAI_CURRENT_APIS_SSOT.md`](OPENAI_CURRENT_APIS_SSOT.md) - API discovery findings
- [`EXTRACTED_KEY_INFO.md`](EXTRACTED_KEY_INFO.md) - Key implementation details
- [`CURRENT_STATE_AND_FIX.md`](CURRENT_STATE_AND_FIX.md) - Initial assessment

## 🚦 Quick Start

### 1. Prerequisites
```bash
# Check Python version (3.10+)
python --version

# Check OpenAI SDK version (must be 1.108.1+)
pip show openai
```

### 2. Environment Setup
Create `.env` file:
```bash
# Required
OPENAI_API_KEY=sk-...

# Model Configuration (we have access to all!)
OPENAI_DECISION_MODEL=gpt-5        # or gpt-4o
CUA_MODEL=computer-use-preview     # or gpt-4o

# Feature Flags
ENABLE_CUA=1                        # Use Computer Use
ENABLE_PLAYWRIGHT=1                 # Playwright fallback

# YC Credentials (for auto-login)
YC_EMAIL=your_email@example.com
YC_PASSWORD=your_password

# Safety Settings
DAILY_QUOTA=25
WEEKLY_QUOTA=120
PACE_MIN_SECONDS=45
```

### 3. Install & Run
```bash
# Install dependencies
make setup

# Install Playwright browsers (local)
make browsers

# Run the application
PYTHONPATH=src make run

# Or directly:
PYTHONPATH=src streamlit run src/yc_matcher/interface/web/ui_streamlit.py
```

### 4. Using the Bot
1. Open http://localhost:8501
2. Fill in 3 inputs:
   - **Your Profile**: Who you are
   - **Match Criteria**: What you're looking for
   - **Message Template**: How to reach out
3. Select decision mode (Advisor/Rubric/Hybrid)
4. Click "Start Autonomous Browsing"
5. Monitor progress and approve messages (if in Advisor mode)

## 🔧 Key Commands

```bash
make setup          # Install dependencies
make browsers       # Install Playwright
make run           # Launch UI
make test          # Run tests
make verify        # Lint + type check + tests
make check-cua     # Verify Computer Use access
```

## 📊 Available Models (Verified Access)

### GPT Models
- ✅ gpt-4, gpt-4o, gpt-4o-mini
- ✅ **gpt-5**, gpt-5-mini, gpt-5-nano
- ✅ gpt-4.1, gpt-4.1-mini, gpt-4.1-nano

### Computer Use
- ✅ **computer-use-preview**
- ✅ computer-use-preview-2025-03-11

### O-Series
- ✅ o1, o3, o3-mini
- ✅ o3-deep-research

## 🛡️ Safety Features

- **STOP Flag**: `.runs/stop.flag` halts execution immediately
- **Quotas**: Daily/weekly limits enforced
- **Deduplication**: Never messages same person twice
- **Shadow Mode**: Test without sending
- **Pacing**: Minimum delay between sends
- **Audit Trail**: JSONL event logging

## 🏗️ Architecture

```
src/yc_matcher/
├── domain/          # Pure business logic
├── application/     # Use cases
├── infrastructure/  # External adapters
│   ├── ai/         # OpenAI integration
│   ├── browser/    # CUA & Playwright
│   └── storage/    # SQLite repositories
└── interface/       # Entry points
    └── web/        # Streamlit UI
```

## 📈 Decision Modes

1. **Advisor Mode**: AI evaluates, requires manual approval
2. **Rubric Mode**: Deterministic scoring, auto-sends if threshold met
3. **Hybrid Mode**: Combines AI + rubric, auto-sends if threshold met

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No module named 'yc_matcher'" | Use `PYTHONPATH=src` prefix |
| "responses API not found" | Upgrade SDK: `pip install --upgrade openai` |
| "Browser not launching" | Run `make browsers` |
| "Invalid parameter: response_format" | Fixed in latest code |
| "Model not found" | Check available models with `check_models.py` |

## 📝 Recent Updates

- **December 2025**: Confirmed Responses API exists and works
- **December 2025**: Fixed GPT-4 response_format issue
- **December 2025**: Verified GPT-5 and Computer Use access
- **December 2025**: Documentation fully refactored

## 🔗 Links

- YC Cofounder Matching: https://www.startupschool.org/cofounder-matching
- OpenAI Platform: https://platform.openai.com/
- Repository: [Current Repository]

---

**Status**: Ready to run with minimal configuration needed!