# OpenAI API Reference - Single Source of Truth

> 📌 **This is the ONLY reference you need for OpenAI API usage in this codebase.**
> 
> All information verified via Context7 MCP - December 2025

---

## 🎯 Quick Reference

### GPT-5 Decision Making
```python
from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model="gpt-5",
    input=[
        {"role": "system", "content": "Your instructions"},
        {"role": "user", "content": "User input"}
    ],
    # CRITICAL: These are NESTED objects, not top-level
    text={
        "verbosity": "low"      # low/medium/high
    },
    reasoning={
        "effort": "minimal"     # minimal/low/medium/high (speed vs depth)
    },
    max_output_tokens=4000,     # Default 4000, max 128,000
    temperature=0.3,            # 0-2 range (lower = more focused)
    top_p=0.9,                  # Nucleus sampling (alternative to temperature)
    truncation="auto",          # Handle long contexts
    store=True,                 # Save for retrieval
    service_tier="auto"         # auto/default/flex/priority
)
```

### GPT-4 Fallback
```python
# When GPT-5 not available, use Chat Completions
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "Your instructions"},
        {"role": "user", "content": "User input"}
    ],
    response_format={"type": "json_object"},
    temperature=0.3,
    max_tokens=800  # Note: "max_tokens" not "max_output_tokens" for GPT-4
)
```

### Computer Use (CUA)
```python
response = client.responses.create(
    model="computer-use-preview",  # From your Models endpoint
    input="Click the submit button",
    tools=[{
        "type": "computer_use_preview",
        "display_width": 1280,
        "display_height": 800
    }],
    max_output_tokens=1024,  # CUA model limit
    truncation="auto",
    previous_response_id=prev_id  # For multi-turn
)

# Handle computer call
if response.output and hasattr(response.output[0], 'computer_call'):
    # Execute with Playwright
    await page.click(response.output[0].computer_call.coordinates)
    
    # Send screenshot back
    screenshot = await page.screenshot()
    client.responses.create(
        previous_response_id=response.id,
        computer_call_output={
            "call_id": response.output[0].computer_call.call_id,
            "screenshot": base64.b64encode(screenshot).decode()
        }
    )
```

---

## 📊 Parameter Reference Table

| Parameter | GPT-5 Value | GPT-4 Value | CUA Value | Notes |
|-----------|------------|-------------|-----------|--------|
| **Model ID** | `gpt-5` | `gpt-4o` | `computer-use-preview` | NOT `gpt-5-thinking` |
| **API** | Responses API | Chat Completions | Responses API | Different endpoints |
| **Max Output** | 4000 default, 128k max | 800 default | 1024 max | GPT-5 has huge capacity |
| **Context Window** | 400,000 tokens | 128,000 tokens | 8,192 tokens | Input capacity |
| **Temperature** | 0-2 | 0-2 | 0-2 | Lower = more focused |
| **Verbosity** | `text.verbosity` | N/A | N/A | Nested in text object! |
| **Reasoning** | `reasoning.effort` | N/A | N/A | For speed optimization |

---

## ⚙️ Environment Variables

Add these to your `.env` file:

```bash
# OpenAI API
OPENAI_API_KEY=sk-...                  # Required

# Decision Model (GPT-5 or GPT-4 fallback)
OPENAI_DECISION_MODEL=gpt-5            # Use gpt-5 if available
GPT5_MAX_TOKENS=4000                   # Up to 128,000
GPT5_TEMPERATURE=0.3                   # 0-2 range
GPT5_TOP_P=0.9                         # Nucleus sampling
GPT5_VERBOSITY=low                     # low/medium/high
GPT5_REASONING_EFFORT=minimal          # minimal/low/medium/high
SERVICE_TIER=auto                      # auto/default/flex/priority

# Computer Use
CUA_MODEL=computer-use-preview         # From your Models endpoint
CUA_MAX_TOKENS=1024                    # CUA limit
CUA_TEMPERATURE=0.3                    # For CUA responses
CUA_MAX_TURNS=40                       # Loop limit
```

---

## 🔍 Response Parsing

### GPT-5 Response Structure
```python
# GPT-5 returns an output array with reasoning and message items
response = client.responses.create(...)

# Method 1: Use SDK helper (preferred)
content = response.output_text  # Aggregates all text

# Method 2: Manual parsing (fallback)
text_parts = []
for item in response.output:
    if item.type == "reasoning":
        # Log but skip reasoning items
        continue
    elif item.type == "message":
        if isinstance(item.content, list):
            for content_item in item.content:
                if hasattr(content_item, "text"):
                    text_parts.append(content_item.text)
        elif isinstance(item.content, str):
            text_parts.append(item.content)

content = "".join(text_parts)
```

### GPT-4 Response Structure
```python
# GPT-4 uses simpler structure
response = client.chat.completions.create(...)
content = response.choices[0].message.content
```

---

## 🚨 Common Mistakes to Avoid

### ❌ WRONG
```python
# Top-level verbosity (WRONG!)
params = {
    "verbosity": "low",  # ❌ Not nested
    "max_output_tokens": 800  # ❌ Too small
}

# Using max_tokens for GPT-5 (WRONG!)
params = {
    "max_tokens": 4000  # ❌ Should be max_output_tokens
}

# Using gpt-5-thinking (WRONG!)
model = "gpt-5-thinking"  # ❌ No such model
```

### ✅ CORRECT
```python
# Nested parameters (CORRECT!)
params = {
    "text": {"verbosity": "low"},  # ✅ Nested
    "reasoning": {"effort": "minimal"},  # ✅ Nested
    "max_output_tokens": 4000  # ✅ Correct size and param name
}

# Correct model ID
model = "gpt-5"  # ✅ Correct
```

---

## 🔄 Fallback Strategy

Always implement fallback for unsupported parameters:

```python
try:
    # Try with all parameters
    params = {
        "model": "gpt-5",
        "input": input_data,
        "text": {"verbosity": "low"},
        "reasoning": {"effort": "minimal"},
        "response_format": {"type": "json_schema", ...},
        "max_output_tokens": 4000
    }
    response = client.responses.create(**params)
except Exception as e:
    # Remove potentially unsupported params
    params.pop("response_format", None)
    params.pop("text", None)
    params.pop("reasoning", None)
    # Retry
    response = client.responses.create(**params)
```

---

## 📝 Multi-turn Conversations

Use `previous_response_id` for context:

```python
# First turn
response1 = client.responses.create(
    model="gpt-5",
    input="First question"
)

# Second turn (maintains context)
response2 = client.responses.create(
    model="gpt-5",
    input="Follow-up question",
    previous_response_id=response1.id  # Links to previous
)
```

---

## 🔗 Key Files in Codebase

| File | Purpose | Uses |
|------|---------|------|
| `src/yc_matcher/infrastructure/ai/openai_decision.py` | GPT-5/4 decisions | Responses API with fallback |
| `src/yc_matcher/infrastructure/browser/openai_cua.py` | Computer Use | Responses API + Playwright |
| `src/yc_matcher/config.py` | Configuration | All env var handling |
| `.env.example` | Environment template | Copy and fill values |

---

## ✅ Verification Checklist

Before using OpenAI APIs:

1. [ ] Check model availability: `client.models.list()`
2. [ ] Verify API key has GPT-5 access (not all do)
3. [ ] Set all environment variables
4. [ ] Test with small token limits first
5. [ ] Monitor costs (GPT-5 is expensive)
6. [ ] Implement proper error handling
7. [ ] Add fallback to GPT-4 if needed

---

## 📚 Additional Resources

- **Context7 Truth**: [CONTEXT7_TRUTH.md](./CONTEXT7_TRUTH.md) - Detailed Context7 findings
- **Implementation Summary**: [CONTEXT7_IMPLEMENTATION_SUMMARY.md](./CONTEXT7_IMPLEMENTATION_SUMMARY.md)
- **OpenAI Platform**: https://platform.openai.com/docs
- **Context7 MCP**: Use `use context7` in prompts for latest docs

---

## ⚠️ Important Notes

1. **Not all accounts have GPT-5** - Always check availability
2. **SDK versions matter** - Some parameters need latest SDK
3. **Costs add up** - GPT-5 is significantly more expensive
4. **Rate limits apply** - Implement exponential backoff
5. **Parameters evolve** - Use Context7 MCP for latest info

---

*Last updated: December 2025 | Verified with Context7 MCP*
*When in doubt, query Context7: "Show me latest GPT-5 API docs. use context7"*