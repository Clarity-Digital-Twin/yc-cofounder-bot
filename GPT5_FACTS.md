# GPT-5 FACTS - THE TRUTH (August 2025)

## ✅ CONFIRMED FACTS ABOUT GPT-5

### 1. GPT-5 EXISTS (Released August 7, 2025)
- **Model ID**: `gpt-5` (NOT `gpt-5-thinking`)
- **Variants**: `gpt-5`, `gpt-5-mini`, `gpt-5-nano`
- **API**: Uses the new **Responses API**, NOT Chat Completions

### 2. API Access Requirements
- **Tier Access**: Available on Tiers 1-5 (but not all API keys have it)
- **Project-Specific**: Some projects may not have access even with valid API key
- **Verification**: Run `client.models.list()` to check availability

### 3. Correct API Usage (Responses API)
```python
# CORRECT - GPT-5 uses Responses API
response = client.responses.create(
    model="gpt-5",
    input=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"}
    ],
    reasoning_effort="medium",  # GPT-5 specific
    verbosity="normal",  # GPT-5 specific
    max_completion_tokens=800,  # NOT max_tokens!
)

# WRONG - This will fail with GPT-5
response = client.chat.completions.create(
    model="gpt-5",  # Will error!
    messages=[...],
    max_tokens=800  # Wrong parameter name!
)
```

### 4. Key Differences from GPT-4
- **Different API**: Responses API vs Chat Completions
- **Different parameters**: 
  - `max_completion_tokens` instead of `max_tokens`
  - `reasoning_effort` (minimal/low/medium/high)
  - `verbosity` (short/normal/long)
- **Pricing**: $1.25/1M input, $10/1M output

### 5. Common Errors and Solutions

#### Error: "model_not_found"
**Cause**: Your API key/project doesn't have GPT-5 access
**Solution**: Use fallback to GPT-4 or get new API key with access

#### Error: "unsupported_parameter: max_tokens"
**Cause**: Using Chat Completions API with GPT-5
**Solution**: Use Responses API with `max_completion_tokens`

## 🔴 MYTHS TO FORGET

1. **MYTH**: "gpt-5-thinking" is the model name
   **TRUTH**: It's just `gpt-5`

2. **MYTH**: GPT-5 works with Chat Completions API
   **TRUTH**: GPT-5 requires Responses API

3. **MYTH**: All OpenAI accounts have GPT-5
   **TRUTH**: Project-specific access varies

## 📋 Implementation Checklist

- [x] Model ID is `gpt-5` not `gpt-5-thinking`
- [x] Using Responses API for GPT-5
- [x] Using `max_completion_tokens` not `max_tokens`
- [x] Fallback to GPT-4 when GPT-5 unavailable
- [x] Check models.list() before assuming access

## 🚀 Working Code Pattern

```python
def get_best_model(client):
    """Get best available model with fallback."""
    models = client.models.list()
    available = [m.id for m in models.data]
    
    if "gpt-5" in available:
        return "gpt-5"
    elif "gpt-4o" in available:
        return "gpt-4o"
    elif "gpt-4-turbo" in available:
        return "gpt-4-turbo"
    else:
        return "gpt-4"  # Final fallback

def call_model(client, model, prompt):
    """Call model with correct API."""
    if model.startswith("gpt-5"):
        # Use Responses API
        return client.responses.create(
            model=model,
            input=[{"role": "user", "content": prompt}],
            max_completion_tokens=1000
        )
    else:
        # Use Chat Completions for GPT-4
        return client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
```

## 🔑 Environment Variables

```bash
# Correct
OPENAI_DECISION_MODEL=gpt-5

# Wrong
OPENAI_DECISION_MODEL=gpt-5-thinking  # Doesn't exist!
```

---

**Last Updated**: August 22, 2025
**Verified Working**: Yes, with correct API key