Project Structure

Packaging Strategy
- Distribute as a Python package with a console script for the CLI and an optional Streamlit app. Keep internal modules small and single‑purpose.

Proposed Layout
```
yc-matcher/
  docs/
  src/
    yc_matcher/
      __init__.py
      decision.py         # Paste-mode decisioning: yes/no + rationale + draft
      agent.py            # Semi-auto agent wiring, tools registration
      computer.py         # Playwright-backed Computer adapter
      config.py           # Settings (env + CLI/Streamlit), validation
      run_cli.py          # CLI entrypoint (fallback)
      ui_streamlit.py     # Preferred UI: criteria, template, paste, results
      storage.py          # JSON counter + optional SQLite session
      templates.py        # Message templates and tone helpers
      scoring.py          # Simple heuristics (optional)
  tests/
    test_quota_guard.py
    test_templates.py
    test_scoring.py
  pyproject.toml
  Makefile
  .env.example
  .pre-commit-config.yaml
  README.md
```

Entrypoints
- Streamlit: `streamlit run -m yc_matcher.ui_streamlit`
- CLI: `yc-matcher` (console_script) → `yc_matcher.run_cli:main`

Configuration
- `.env` for secrets + defaults; CLI flags override.
- Keep all config typed/validated in `config.py` (Pydantic).
