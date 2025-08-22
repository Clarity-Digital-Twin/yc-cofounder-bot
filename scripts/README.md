# Scripts Directory

Utility and testing scripts for the YC Cofounder Bot.

## 🧪 Testing Scripts

- `run_full_test.py` - Complete end-to-end test with browser automation
- `test_decision_engine.py` - Test GPT decision making
- `test_gpt41.py` - Test GPT-4.1 model availability
- `check_models.py` - List available OpenAI models

## 🏃 Running Scripts

```bash
# Run full test
uv run python scripts/run_full_test.py

# Check available models
uv run python scripts/check_models.py

# Test decision engine
uv run python scripts/test_decision_engine.py
```

## 📝 Manual Test Scripts

Additional manual test scripts are in `tests/manual/` for specific UI and browser testing scenarios.