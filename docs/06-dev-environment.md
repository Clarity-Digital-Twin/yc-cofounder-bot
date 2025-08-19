Developer Environment

Baseline
- Python: 3.11+
- Package manager: `uv`
- Browser automation: Playwright (Chromium)
- OpenAI SDK + Agents SDK

Packages (initial)
- Runtime: `openai`, `openai-agents`, `playwright`, `python-dotenv`, `pydantic`
- UI (preferred for MVP): `streamlit`
- Dev: `pytest`, `pytest-asyncio`, `mypy`, `ruff`, `pre-commit`, `types-requests`

Environment Variables
- `OPENAI_API_KEY` — required
- `YC_MATCH_URL` — target start URL
- `MAX_SEND` — default quota (fallback for CLI arg)

Local Setup (once code exists)
- `uv init` (project), then add dependencies.
- `python -m playwright install chromium`
- `pre-commit install`

Makefile Targets (planned)
- `make setup` — install deps + browsers
- `make lint` — ruff + mypy
- `make test` — pytest
- `make run` — run Streamlit UI with defaults
