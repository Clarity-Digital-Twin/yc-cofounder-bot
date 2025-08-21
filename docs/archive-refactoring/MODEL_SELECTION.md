# Model Selection and Configuration

## Overview

This project uses two distinct models:

1. **Computer Use Model** (`CUA_MODEL`) - Analyzes screenshots via Responses API
2. **Decision Model** (`OPENAI_DECISION_MODEL`) - Evaluates matches for Advisor/Hybrid modes

## Critical: How CUA Actually Works

**YOU provide the browser via Playwright. CUA only analyzes screenshots and suggests actions.**

See [OPENAI_CUA_IMPLEMENTATION.md](./OPENAI_CUA_IMPLEMENTATION.md) for the correct Responses API approach.

## Environment Configuration

```bash
# Required - Never hardcode these!
CUA_MODEL=<your-computer-use-model>        # From your Models endpoint
OPENAI_DECISION_MODEL=<your-best-model>    # For decision making

# Optional tuning
CUA_TEMPERATURE=0.3                        # Lower = more deterministic
DECISION_TEMPERATURE=0.7                   # Higher = more creative
```

## Model Requirements

### Computer Use Model
- Must support Computer Use via Responses API
- Requires `truncation="auto"` parameter
- Tier 3-5 OpenAI account required
- Check availability: https://platform.openai.com/account/models

### Decision Model  
- Any GPT-4+ class model
- Used for Advisor and Hybrid modes only
- Rubric mode doesn't use LLM (deterministic)

## Decision Modes and Model Usage

| Mode | Uses CUA Model | Uses Decision Model | Auto-Send |
|------|---------------|-------------------|-----------|
| Advisor | ✅ Browsing | ✅ Evaluation | ❌ Never |
| Rubric | ✅ Browsing | ❌ Rules only | ✅ Always |
| Hybrid | ✅ Browsing | ✅ Weighted eval | ✅ If confident |

## Upgrading Models

When new models become available:

1. **Verify Computer Use support**
   ```python
   # Test with new model
   response = client.responses.create(
       model="new-model-name",
       tools=[{"type": "computer_use_preview", ...}],
       truncation="auto"  # Required!
   )
   ```

2. **Update environment**
   ```bash
   export CUA_MODEL=new-computer-use-model
   export OPENAI_DECISION_MODEL=new-gpt-model
   ```

3. **Run validation**
   ```bash
   make test                    # Unit tests
   python scripts/validate_deployment.py  # Acceptance tests
   ```

4. **Monitor metrics**
   - Success rate (target >95%)
   - Latency (target <5s per profile)
   - Cost per profile
   - Decision accuracy

## Acceptance Criteria

Any model configuration must pass:

- [ ] Navigates to YC listing successfully
- [ ] Extracts profile information correctly
- [ ] Makes appropriate decisions per mode
- [ ] Sends messages when criteria met
- [ ] Respects safety features (STOP, quotas)
- [ ] Maintains performance targets

## Cost Optimization

### Computer Use (Expensive)
- Minimize screenshot resolution when possible
- Batch actions to reduce round trips
- Cache repeated page states

### Decision Model (Moderate)
- Use Rubric mode when rules suffice
- Tune prompts for conciseness
- Consider caching similar evaluations

## Fallback Strategy

```python
# Primary: OpenAI CUA via Responses API
if CUA_MODEL and tier_3_plus:
    use_cua_responses_api()
    
# Fallback: Playwright automation
elif ENABLE_PLAYWRIGHT_FALLBACK:
    use_playwright_dom_automation()
    
# Manual: User intervention required
else:
    prompt_user_for_manual_action()
```

## Common Issues

### "Model not found"
- Verify tier 3-5 access
- Check Models endpoint for availability
- Ensure model supports Computer Use

### "Invalid truncation parameter"
- Only use `truncation="auto"` with Computer Use
- Don't use truncation with regular completions

### High latency
- Reduce screenshot size
- Optimize prompts
- Consider regional endpoints

## Testing Model Changes

```bash
# 1. Unit tests for model integration
pytest tests/unit/test_openai_cua_browser.py

# 2. Integration tests for decision modes
pytest tests/integration/test_decision_modes.py

# 3. End-to-end validation
pytest tests/e2e/test_model_acceptance.py

# 4. Performance benchmarks
python scripts/benchmark_models.py
```

## Important Notes

- **Never hardcode model names** - Always use environment variables
- **Test thoroughly** - Model behavior can vary significantly
- **Monitor costs** - Computer Use is expensive (~$0.50 per 20 profiles)
- **Have fallbacks** - Models can have outages or degraded performance

For implementation details, see [OPENAI_CUA_IMPLEMENTATION.md](./OPENAI_CUA_IMPLEMENTATION.md)