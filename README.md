YC Co‑Founder Matching Bot

Human‑in‑the‑loop outreach assistant for YC/Startup School cofounder matching.

Docs
- See `docs/` for product scope, architecture, implementation plan, operations/safety, dev setup, project structure, and testing.
- For picking and upgrading models, read `MODEL_SELECTION.md`.

 Quickstart (after dependencies are installed)
- Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
- Set `CUA_MODEL` (Computer Use) and `DECISION_MODEL` per `MODEL_SELECTION.md`.
- Run the Streamlit UI: `make run`
- Paste a profile, get Yes/No + rationale + draft message (template preloaded).

Development
- Install deps: `make setup`
- Lint/format: `make lint` / `make format`
- Types: `make type`
- Tests: `make test`
