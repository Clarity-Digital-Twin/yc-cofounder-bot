# OpenAI API Implementation Guide
*September 2025 - Verified with Context7 MCP*

## Available APIs & Models

### APIs We Use
1. **Chat Completions API** - For GPT-4 decision evaluation
   - Endpoint: `client.chat.completions.create()`
   - Used in: `openai_decision.py`
   - Models: gpt-4, gpt-4-turbo, gpt-4o

2. **Responses API** (Future/Optional) - For stateful conversations
   - Endpoint: `client.responses.create()`
   - Requires: OpenAI SDK v1.108.1+
   - Models: gpt-5, gpt-4o, o-series
   - Features: Built-in tools, state management

### Models Available (Verified)
```python
# GPT-4 Family (Production Ready)
"gpt-4"           # Classic, reliable
"gpt-4-turbo"     # Faster, cheaper
"gpt-4o"          # Multimodal

# GPT-5 Family (If Access Granted)
"gpt-5"           # NOT "gpt-5-thinking"
"gpt-5-mini"      # Smaller, faster
"gpt-5-nano"      # Tiny, ultra-fast

# O-Series (Advanced Reasoning)
"o1-mini"         # Small reasoning model
"o1-preview"      # Preview reasoning model

# Computer Use (Browser Control)
"computer-use-preview"  # Via Responses API only
```

## Implementation Patterns

### GPT-4 Decision Evaluation (Current)
```python
# Working implementation in openai_decision.py
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": profile_data}
    ],
    temperature=0.3,
    max_tokens=800
    # DO NOT use response_format with GPT-4
)
```

### GPT-5 with Responses API (If Available)
```python
# For GPT-5 models specifically
response = client.responses.create(
    model="gpt-5",
    input=[{"type": "user", "content": prompt}],
    max_output_tokens=4000,  # NOT max_tokens
    text={"verbosity": "low"},  # Nested in text object
    reasoning={"effort": "minimal"},  # For speed
    temperature=1.0  # GPT-5 works best at 1.0
)
```

## Key Implementation Notes

### Critical Fixes Applied
1. **GPT-4 Compatibility**: Removed `response_format` parameter (not supported)
2. **Parameter Names**: GPT-5 uses `max_output_tokens`, not `max_tokens`
3. **Model Names**: Use `gpt-5`, NOT `gpt-5-thinking`
4. **SDK Version**: Must be v1.108.1+ for Responses API

### Error Handling Pattern
```python
try:
    # Try with all parameters
    response = client.responses.create(...)
except Exception:
    # Fallback to basic parameters
    response = client.chat.completions.create(...)
```

## Configuration (.env)

```bash
# Model Selection
OPENAI_API_KEY=sk-...
OPENAI_DECISION_MODEL=gpt-4o  # For decisions
CUA_MODEL=computer-use-preview  # For browser control (optional)

# Feature Flags
ENABLE_CUA=0  # Set to 1 only if you have access
USE_RESPONSES_API=0  # Set to 1 for GPT-5 models
```

## Verification Commands

```bash
# Check available models
PYTHONPATH=src python check_models.py

# Test decision evaluation
PYTHONPATH=src python -c "from yc_matcher.infrastructure.ai.openai_decision import test_decision; test_decision()"

# Test Responses API (if available)
python test_responses_api.py
```