YC Co‑Founder Matching Bot

Autonomous browser automation for YC/Startup School cofounder matching using OpenAI Computer Use.

## How It Works

1. **You provide 3 inputs**: Your Profile, Match Criteria, Message Template
2. **CUA+Playwright browse together**: CUA analyzes screenshots, Playwright executes actions
3. **Decisions made**: Using Advisor/Rubric/Hybrid modes per your configuration
4. **Messages sent**: Automatically when thresholds met (with safety controls)

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
