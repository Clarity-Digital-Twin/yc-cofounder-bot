YC Co‑Founder Matching Bot

Autonomous browser automation for YC/Startup School cofounder matching using OpenAI Computer Use.

## How It Works

1. **You provide 3 inputs**: Your Profile, Match Criteria, Message Template
2. **OpenAI CUA browses**: Autonomously navigates YC site via Computer Use API
3. **Decisions made**: Using Advisor/Rubric/Hybrid modes per your configuration
4. **Messages sent**: Automatically when thresholds met (with safety controls)

## Docs
- See `docs/` for complete documentation
- **CRITICAL**: Read `OPENAI_COMPUTER_USE_TRUTH.md` for how CUA actually works
- For model selection: `MODEL_SELECTION.md`

## Quickstart
1. Copy `.env.example` to `.env` and set:
   - `OPENAI_API_KEY=sk-...`
   - `CUA_MODEL=computer-use-preview` (from your Models endpoint)
   - `OPENAI_DECISION_MODEL=<your-best-llm>`
2. Install: `make setup`
3. Run: `make run`
4. Enter your 3 inputs and click RUN

**Note**: YOU provide the browser via Playwright. CUA analyzes screenshots and suggests actions.

Development
- Install deps: `make setup`
- Lint/format: `make lint` / `make format`
- Types: `make type`
- Tests: `make test`
