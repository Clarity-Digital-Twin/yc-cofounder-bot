Project Structure

Packaging Strategy
- Distribute as a Python package with a console script for the CLI and an optional Streamlit app. Keep internal modules small and single‑purpose.

Proposed Layout (DDD-aligned)
```
yc-matcher/
  docs/
  src/
    yc_matcher/
      __init__.py
      domain/
        __init__.py
        entities.py        # Criteria, Profile, Decision, Score (dataclasses)
        services.py        # ScoringService (Strategy)
      application/
        __init__.py
        ports.py           # DecisionPort, MessagePort, QuotaPort, SeenRepo, LoggerPort, BrowserPort
        use_cases.py       # EvaluateProfile, SendMessage, ProcessCandidate
        schema.py          # Pydantic DTOs for model outputs
      infrastructure/
        __init__.py
        openai_decision.py # OpenAIDecisionAdapter (Facade/Adapter)
        sqlite_repo.py     # SQLiteSeenRepo
        jsonl_logger.py    # JSONLLogger
        playwright_browser.py # PlaywrightBrowserAdapter + click_by_text helpers
        quota.py           # Quota implementation
        templates.py       # TemplateRenderer with clamps/safety
      interface/
        __init__.py
        ui_streamlit.py    # Streamlit UI
        run_cli.py         # CLI entrypoint
        di.py              # DI container/factories
      # Transitional modules (existing)
      decision.py          # (to be folded into domain/application)
      templates.py         # (compat shim to infrastructure/templates)
      storage.py           # (legacy JSON counter)
  tests/
    unit/
      test_schema.py
      test_scoring.py
      test_use_cases.py
    integration/
      test_openai_decision.py
      test_sqlite_repo.py
      test_playwright_browser.py
    e2e/
      test_shadow_mode.md  # manual checklist
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
 - Adhere to dependency rules: interface→application→domain; infra implements application ports.
