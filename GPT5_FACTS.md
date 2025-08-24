# GPT-5 FACTS - DEPRECATED (See CONTEXT7_TRUTH.md)

⚠️ **THIS DOCUMENT CONTAINS OUTDATED/INCORRECT INFORMATION**

**Please use [CONTEXT7_TRUTH.md](./CONTEXT7_TRUTH.md) for accurate, Context7 MCP-verified documentation.**

---

# GPT-5 FACTS - OUTDATED (August 2025)

## ✅ CONFIRMED FACTS FROM OFFICIAL OPENAI DOCS

### 1. GPT-5 Models & Availability
- **Model IDs**: `gpt-5`, `gpt-5-mini`, `gpt-5-nano` (confirmed August 2025 release)
- **API**: Uses **Responses API** (`client.responses.create()`)
- **Context Window**: 400,000 tokens (GPT-5), 128,000 tokens (GPT-5 Chat)
- **Max Output**: 128,000 tokens (GPT-5), 16,384 tokens (GPT-5 Chat)
- **Knowledge Cutoff**: September 30, 2024

### 2. CORRECT API Parameters (From Context7 Docs)

#### ✅ SUPPORTED Parameters for GPT-5:
```python
response = client.responses.create(
    model="gpt-5",                      # Required
    input=[...],                         # Required (not "messages")
    max_output_tokens=4000,              # Supported (up to 128,000!)
    temperature=0.7,                     # Supported (0 to 2)
    top_p=0.9,                          # Supported (nucleus sampling)
    top_logprobs=5,                     # Supported (0 to 20)
    instructions="System prompt",        # Supported (system message)
    previous_response_id="resp_123",    # Supported (multi-turn)
    truncation="auto",                  # Supported ("auto" or "disabled")
    store=True,                         # Supported (save response)
    stream=False,                       # Supported (streaming)
    parallel_tool_calls=True,           # Supported
    metadata={"key": "value"},          # Supported (16 key-value pairs)
    prompt_cache_key="cache_key",       # Supported (caching)
    safety_identifier="user_hash",      # Supported (safety tracking)
    service_tier="auto",                # Supported ("auto", "default", "flex", "priority")
)
```

#### ⚠️ PARAMETERS WITH CAVEATS:
- **reasoning**: Only for GPT-5 and o-series models (configuration object)
- **text**: Configuration for text response format
- **response_format**: MAY NOT be in current SDK yet
- **verbosity**: Docs show it exists but SDK support varies
- **reasoning_effort**: New "minimal" option for faster responses (SDK pending)

#### ❌ NEVER USE WITH GPT-5:
- `messages` - Use `input` instead
- `max_tokens` - Use `max_output_tokens`
- `user` - Deprecated, use `safety_identifier` and `prompt_cache_key`

### 3. Response Parsing (From Context7)

```python
# CORRECT - Use output_text helper (aggregates all text)
response = client.responses.create(...)
content = response.output_text  # Recommended by docs

# FALLBACK - Manual parsing if needed
if hasattr(response, 'output') and isinstance(response.output, list):
    for item in response.output:
        if hasattr(item, 'type'):
            if item.type == 'message':
                # Extract message content
                pass
            elif item.type == 'reasoning':
                # Skip reasoning traces
                pass
```

### 4. Token Limits - MASSIVE CAPACITY

| Model | Context Window | Max Output | You're Using |
|-------|---------------|------------|--------------|
| GPT-5 | 400,000 | 128,000 | 800 (0.6%!) |
| GPT-5 Chat | 128,000 | 16,384 | 800 (4.9%) |
| GPT-4o | 128,000 | 16,384 | 800 |

**YOU'RE WASTING 99.4% OF GPT-5'S OUTPUT CAPACITY!**

### 5. Error Handling Pattern

```python
def call_gpt5_with_fallback(client, params):
    """Try with all params, fall back on errors."""
    try:
        # Try with all optional params
        return client.responses.create(**params)
    except Exception as e:
        if "unsupported_parameter" in str(e):
            # Remove problematic params
            params.pop("response_format", None)
            params.pop("verbosity", None)
            params.pop("reasoning_effort", None)
            params.pop("temperature", None)
            
            # Add JSON instruction to prompt
            params["input"][-1]["content"] += "\n\nReturn JSON with keys: ..."
            
            # Retry with minimal params
            return client.responses.create(**params)
```

## 🔴 DOCUMENTATION CONTRADICTIONS FOUND

| Your Docs Say | Context7 Says | Reality |
|--------------|---------------|---------|
| "NO verbosity" | verbosity exists | Parameter exists but SDK support varies |
| "NO response_format" | text config exists | Has text config, response_format pending |
| "max_output_tokens: 800" | Can use 128,000 | You're using <1% capacity |
| "NO temperature" | temperature: 0-2 | Fully supported |

## 📋 IMMEDIATE FIXES NEEDED

1. **Increase Token Limit**:
   ```python
   "max_output_tokens": 4000  # From 800 - 5x improvement
   ```

2. **Add Temperature Control**:
   ```python
   "temperature": float(os.getenv("GPT5_TEMPERATURE", "0.3"))
   ```

3. **Use Multi-Turn Conversations**:
   ```python
   "previous_response_id": last_response.id if last_response else None
   ```

4. **Enable Streaming for Long Responses**:
   ```python
   "stream": True  # For real-time output
   ```

## 🚀 OPTIMIZED IMPLEMENTATION

```python
def create_gpt5_response(client, prompt, system_prompt=None, **kwargs):
    """Create GPT-5 response with all optimizations."""
    params = {
        "model": "gpt-5",
        "input": [],
        "max_output_tokens": min(
            int(os.getenv("GPT5_MAX_TOKENS", "4000")),
            128000  # Model limit
        ),
        "temperature": float(os.getenv("GPT5_TEMPERATURE", "0.3")),
        "top_p": float(os.getenv("GPT5_TOP_P", "0.9")),
        "truncation": "auto",  # Handle long contexts gracefully
        "store": True,  # Save for retrieval
        "service_tier": os.getenv("SERVICE_TIER", "auto"),
    }
    
    # Add system prompt if provided
    if system_prompt:
        params["instructions"] = system_prompt
    
    # Build input
    params["input"].append({"role": "user", "content": prompt})
    
    # Merge additional kwargs
    params.update(kwargs)
    
    try:
        response = client.responses.create(**params)
        return response.output_text
    except Exception as e:
        # Fallback logic here
        pass
```

## 🔑 Environment Variables (CORRECTED)

```bash
# CORRECT - Aligned with Context7 docs
OPENAI_DECISION_MODEL=gpt-5              # Model ID
GPT5_MAX_TOKENS=4000                     # Up from 800
GPT5_TEMPERATURE=0.3                     # For consistency
GPT5_TOP_P=0.9                           # Nucleus sampling
SERVICE_TIER=auto                        # Or "priority" for faster

# WRONG
OPENAI_DECISION_MODEL=gpt-5-thinking     # Doesn't exist
GPT5_VERBOSITY=low                       # SDK doesn't support yet
GPT5_REASONING_EFFORT=minimal            # SDK doesn't support yet
```

## 📊 Performance Impact

By fixing these issues:
- **5x more content** in responses (800 → 4000 tokens)
- **Consistent outputs** with temperature control
- **Faster responses** with service tier selection
- **Better caching** with prompt_cache_key
- **Safer operation** with truncation="auto"

---

**Source**: OpenAI Platform Docs via Context7 MCP
**Last Verified**: August 24, 2025
**SDK Version Required**: openai>=1.101.0