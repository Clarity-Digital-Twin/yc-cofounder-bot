# YC Co-Founder Matcher Bot 🤖

Autonomous browser automation for YC/Startup School cofounder matching using OpenAI Computer Use API and Playwright.

## 🚀 Features

- **Autonomous Browsing**: Automatically browse and evaluate co-founder profiles
- **Smart Decision Making**: Three configurable decision modes (Advisor/Rubric/Hybrid)
- **OpenAI Computer Use**: Vision models understand and interact with web pages
- **Safety First**: Shadow mode, quotas, STOP flags, and deduplication
- **Clean Architecture**: Domain-Driven Design with SOLID principles

## 📋 Quick Start

```bash
# Clone and setup
git clone https://github.com/Clarity-Digital-Twin/yc-cofounder-bot.git
cd yc-cofounder-bot
make setup

# Configure (copy .env.example to .env and add your OpenAI key)
cp .env.example .env

# Run the web UI
make run
```

Then open http://localhost:8502 and provide:
1. **Your Profile**: Brief description of yourself
2. **Match Criteria**: What you're looking for in a co-founder  
3. **Message Template**: Outreach template with {name} placeholder

## Docs
- See `docs/` for complete documentation
- **CRITICAL**: Read `CUA_PLAYWRIGHT_RELATIONSHIP.md` for how CUA+Playwright work together
- For model selection: `MODEL_SELECTION.md`

## Quickstart
1. Copy `.env.example` to `.env` and set:
   - `OPENAI_API_KEY=sk-...`
   - `CUA_MODEL=computer-use-preview` (from your Models endpoint)
   - `OPENAI_DECISION_MODEL=<your-best-llm>`
2. Install: `make setup`
3. Run: `make run`
4. Enter your 3 inputs and click RUN

**Critical Understanding**: CUA and Playwright work TOGETHER - CUA analyzes/plans, Playwright executes. They are not alternatives!

Development
- Install deps: `make setup`
- Lint/format: `make lint` / `make format`
- Types: `make type`
- Tests: `make test`
