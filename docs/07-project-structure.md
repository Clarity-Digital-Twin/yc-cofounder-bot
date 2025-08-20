Project Structure

Packaging Strategy
- Single repo with Streamlit UI and CLI entrypoint. Keep modules small and single‑purpose. Follow DDD with explicit ports/adapters.

Proposed Layout (DDD-aligned)
```
yc-cofounder-bot/
  docs/
  src/
    app/
      __init__.py
      domain/
        __init__.py
        entities/          # UserProfile, MatchCriteria, Decision
        services/          # Scoring, extraction, message rendering
      application/
        __init__.py
        ports.py           # ComputerUsePort, DecisionPort, QuotaPort, SeenRepo, LoggerPort, StopController
        use_cases.py       # DiscoverProfiles, EvaluateAndMessage, ProcessBatch
        dto.py             # Pydantic DTOs for events/decisions
      infrastructure/
        __init__.py
        cua/
          anthropic.py     # AnthropicCUAAdapter (PRIMARY)
          openai.py        # OpenAICUAAdapter (when available)
        browser/
          playwright.py    # PlaywrightBrowserAdapter (FALLBACK)
        storage/
          sqlite_quota.py  # SQLiteQuotaRepo
          sqlite_seen.py   # SQLiteSeenRepo
          jsonl_logger.py  # JSONLLogger
        decision/
          advisor.py       # AdvisorDecisionAdapter (LLM-only)
          rubric.py        # RubricDecisionAdapter (deterministic)
          hybrid.py        # HybridDecisionAdapter (combined)
        messaging/
          templates.py     # Template renderer with clamps/safety
      interface/
        __init__.py
        web/
          ui_streamlit.py  # Streamlit dashboard
        cli/
          main.py          # CLI entrypoint
        di.py              # DI factories (compose ports/adapters)
  tests/
    unit/
      test_decision_math.py
      test_hard_rules.py
      test_template_render.py
      test_stop_quota_dedupe.py
    contract/
      test_computer_use_port.py
    integration/ (opt-in)
      test_playwright_fallback.py
  pyproject.toml
  Makefile
  .env.example
  .pre-commit-config.yaml
  README.md
```

Entrypoints
- Streamlit: `make run` (or `streamlit run src/app/interface/web/ui_streamlit.py`)
- CLI: `python -m app.interface.cli.main`

Configuration
- `.env` for flags and secrets; UI toggles mirror env.
- Typed config via Pydantic; DI composes adapters per `CUA_PROVIDER` and `DECISION_MODE`.
- Adhere to dependency rules: interface→application→domain; infra implements application ports.
