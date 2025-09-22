# YC Co-Founder Bot Documentation

## Quick Links

### 🚀 Getting Started
- [Project Status & Quick Start](technical/PROJECT_STATUS.md) - Current state and how to run
- [Development Environment](development/06-dev-environment.md) - Setup instructions

### 📖 Core Documentation
- [Product Brief](core/01-product-brief.md) - What this bot does
- [Architecture](core/03-architecture.md) - System design
- [Operations & Safety](core/05-operations-and-safety.md) - Safety mechanisms

### 🔧 Technical Reference
- [OpenAI API Guide](technical/OPENAI_API_GUIDE.md) - API usage patterns
- [YC UI Structure](technical/YC_UI_STRUCTURE.md) - Browser automation details
- [Event Schema](technical/event_schema.md) - Logging format

### 💻 Development
- [Project Structure](development/07-project-structure.md) - Code organization
- [Engineering Guidelines](development/11-engineering-guidelines.md) - Clean code practices
- [Testing & Quality](development/08-testing-quality.md) - Test strategy

## Project Overview

A bot that automates finding co-founders on YC's Startup School platform by:

1. **Browsing** profiles automatically using Playwright
2. **Evaluating** matches with GPT-4 AI
3. **Messaging** high-quality candidates

## Current Status (September 2025)

✅ **Core functionality working** - Browser automation, AI evaluation, and messaging all functional

⚙️ **Configuration needed** - Set YC credentials and OpenAI API key in `.env`

📋 **One known fix applied** - Removed unsupported `response_format` parameter for GPT-4

## File Organization

```
docs/
├── README.md              # This file
├── core/                  # Product & design docs
├── technical/             # Implementation details
├── development/           # Dev setup & guidelines
└── archive/              # Historical/outdated docs
```

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

- **September 2025**: Confirmed Responses API exists and works
- **September 2025**: Fixed GPT-4 response_format issue
- **September 2025**: Verified GPT-5 and Computer Use access
- **September 2025**: Documentation fully refactored

## 🔗 Links

- YC Cofounder Matching: https://www.startupschool.org/cofounder-matching
- OpenAI Platform: https://platform.openai.com/
- Repository: [Current Repository]

---

**Status**: Ready to run with minimal configuration needed!