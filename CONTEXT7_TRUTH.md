# Context7 API Documentation Findings - December 2025

## Executive Summary
This document contains the REAL, VERIFIED OpenAI API documentation retrieved from Context7 MCP server.
All information here supersedes any existing documentation in this codebase.

---

## 🚨 CRITICAL FINDINGS FROM CONTEXT7

### GPT-5 Responses API - ACTUAL PARAMETERS

Based on Context7's official OpenAI documentation:

#### 1. **Verbosity Parameter** ✅ CONFIRMED SUPPORTED
```python
# CORRECT - From Context7 Documentation
client.responses.create(
    model="gpt-5",
    input="Your prompt here",
    text={
        "verbosity": "low"  # SUPPORTED: low, medium, high
    }
)
```
- **Location**: In `text` object, NOT top-level
- **Values**: `"low"`, `"medium"`, `"high"`
- **Purpose**: Controls response verbosity/length

#### 2. **Reasoning Effort Parameter** ✅ CONFIRMED SUPPORTED
```python
# CORRECT - From Context7 Documentation
client.responses.create(
    model="gpt-5",
    input="Your prompt here",
    reasoning={
        "effort": "minimal"  # For faster responses
    }
)
```
- **Location**: In `reasoning` object
- **Values**: `"minimal"`, `"low"`, `"medium"`, `"high"`
- **Purpose**: Trade-off between speed and reasoning depth

#### 3. **Max Output Tokens** ✅ CONFIRMED
```python
# CORRECT - From Context7 Documentation
client.responses.create(
    model="gpt-5",
    input="Your prompt here",
    max_output_tokens=128000  # Up to 128k tokens!
)
```
- **Maximum**: 128,000 tokens
- **Context Window**: 400,000 tokens
- **Knowledge Cutoff**: September 30, 2024

#### 4. **Previous Response ID** ✅ CONFIRMED (Multi-turn)
```python
# CORRECT - For multi-turn conversations
response = client.responses.create(
    model="gpt-5",
    input="Follow-up question",
    previous_response_id=previous_response.id  # Chain responses
)
```

#### 5. **Temperature** ✅ CONFIRMED SUPPORTED
```python
# CORRECT - From Context7 Documentation
client.responses.create(
    model="gpt-5",
    input="Your prompt here",
    temperature=0.7,  # 0 to 2
    top_p=0.9  # Alternative to temperature
)
```

---

## 🖥️ COMPUTER USE API - ACTUAL IMPLEMENTATION

### Computer Use Preview Model Specs (From Context7)
- **Model ID**: `computer-use-preview`
- **Context Window**: 8,192 tokens
- **Max Output**: 1,024 tokens
- **Knowledge Cutoff**: October 1, 2023
- **APIs**: Responses API ONLY (not Chat Completions for computer use)
- **Pricing**: $3.00/1M input tokens, $12.00/1M output tokens

### Correct Computer Use Implementation
```python
# CORRECT - From Context7 Documentation
response = client.responses.create(
    model=os.getenv("CUA_MODEL"),  # computer-use-preview
    input="Click the submit button",
    tools=[{
        "type": "computer_use_preview",
        "display_width": 1280,
        "display_height": 800
    }],
    previous_response_id=prev_id,  # For multi-turn
    truncation="auto"  # Handle context window limits
)

# Handle computer call output
if response.output and hasattr(response.output[0], 'computer_call'):
    computer_call = response.output[0].computer_call
    # Execute with Playwright
    await page.click(computer_call.coordinates)
    
    # Send result back
    screenshot = await page.screenshot()
    client.responses.create(
        previous_response_id=response.id,
        computer_call_output={
            "call_id": computer_call.call_id,
            "screenshot": base64.b64encode(screenshot).decode()
        }
    )
```

---

## 📊 COMPARISON: CONTEXT7 DOCS VS. CODEBASE

### ❌ CRITICAL ISSUES FOUND

| Component | Context7 Says | Our Code Does | Status |
|-----------|---------------|---------------|--------|
| **Verbosity** | `text: { verbosity: "low" }` (nested) | Top-level `verbosity` | ❌ WRONG |
| **Max Tokens** | Up to 128,000 | Using 800 (0.6%!) | ❌ SEVERELY LIMITED |
| **Reasoning Effort** | `reasoning: { effort: "minimal" }` | Not using at all | ❌ MISSING OPTIMIZATION |
| **Temperature** | Supported 0-2 | Using but removing on error | ⚠️ CONFUSED |
| **Previous Response ID** | For multi-turn | Not using consistently | ❌ MISSING FEATURE |
| **Truncation** | `"auto"` or `"disabled"` | Not specified | ❌ MISSING |

### ✅ WHAT'S CORRECT

| Component | Implementation | Status |
|-----------|---------------|--------|
| **API Selection** | Using Responses API for GPT-5 | ✅ |
| **Model ID** | Using `gpt-5` not `gpt-5-thinking` | ✅ |
| **Fallback Logic** | Falls back to GPT-4 | ✅ |
| **Response Parsing** | Handles reasoning items | ✅ |
| **Tool Structure** | Computer use tool format | ✅ |

---

## 🔧 REQUIRED CODE FIXES

### 1. Fix Verbosity Parameter Location
```python
# WRONG (current code in openai_decision.py)
params = {
    "model": "gpt-5",
    "input": prompt,
    "verbosity": "low"  # ❌ WRONG LOCATION
}

# CORRECT (per Context7)
params = {
    "model": "gpt-5",
    "input": prompt,
    "text": {
        "verbosity": "low"  # ✅ NESTED IN TEXT
    }
}
```

### 2. Increase Token Limit
```python
# WRONG (current code)
"max_output_tokens": 800  # Using 0.6% of capacity!

# CORRECT (per Context7)
"max_output_tokens": 4000  # Reasonable default
# Can go up to 128000 for long outputs
```

### 3. Add Reasoning Effort for Speed
```python
# Add this for faster responses when deep reasoning not needed
params = {
    "model": "gpt-5",
    "input": prompt,
    "reasoning": {
        "effort": "minimal"  # For speed
    },
    "text": {
        "verbosity": "low"  # For conciseness
    }
}
```

### 4. Use Previous Response ID for Multi-turn
```python
# For Computer Use continuation
if self.prev_response_id:
    params["previous_response_id"] = self.prev_response_id
```

### 5. Add Truncation Strategy
```python
# Add truncation handling
params = {
    "model": "gpt-5",
    "input": prompt,
    "truncation": "auto",  # Automatically handle context limits
    "max_output_tokens": 4000
}
```

---

## 📝 FILES TO UPDATE

### 1. `src/yc_matcher/infrastructure/ai/openai_decision.py`
- Move `verbosity` into `text` object
- Increase `max_output_tokens` to 4000
- Add `reasoning.effort` parameter
- Fix error handling to not remove valid params

### 2. `src/yc_matcher/infrastructure/browser/openai_cua.py`
- Use `previous_response_id` consistently
- Add `truncation: "auto"`
- Fix computer_call_output handling

### 3. Delete/Archive These Contradictory Docs:
- `docs/archive-cleanup/GPT5_FACTS.md` - Contains wrong information
- `GPT5_API_AUDIT_AUG2025.md` - Based on speculation, not Context7

### 4. Update `CLAUDE.md`
- Reference this Context7 truth document
- Remove contradictory statements about verbosity

---

## 🎯 ACTION ITEMS

### Immediate (Breaking Issues)
1. [ ] Move `verbosity` into `text` object in openai_decision.py
2. [ ] Increase `max_output_tokens` from 800 to 4000
3. [ ] Fix parameter removal logic in error handlers

### Performance Improvements
1. [ ] Add `reasoning.effort: "minimal"` for faster responses
2. [ ] Implement `previous_response_id` chaining for CUA
3. [ ] Add `truncation: "auto"` to handle context limits
4. [ ] Make verbosity configurable via env var

### Documentation
1. [ ] Archive old GPT5_FACTS.md
2. [ ] Update CLAUDE.md to reference this doc
3. [ ] Add inline comments with Context7 references

---

## 🔍 SOURCE OF TRUTH

All information in this document comes from:
- **Source**: Context7 MCP Server
- **Library**: /websites/platform_openai
- **Date Retrieved**: December 2025
- **Code Snippets**: 307,361 available examples
- **Trust Score**: 7.5/10 (Official OpenAI docs)

When in doubt, query Context7 again with:
```
Show me GPT-5 Responses API parameters. use context7
```

---

## ⚠️ IMPORTANT NOTES

1. **Model Availability**: Not all API keys have GPT-5 access. Check with `client.models.list()`
2. **Computer Use**: Only works with Responses API, not Chat Completions
3. **Token Costs**: GPT-5 is expensive - use `reasoning.effort: "minimal"` to reduce costs
4. **Deprecation**: Always check OpenAI's deprecation page for updates
5. **SDK Version**: Ensure OpenAI Python SDK is latest version for Responses API support

---

## 🚀 QUICK START CORRECT IMPLEMENTATION

```python
from openai import OpenAI

client = OpenAI()

# For decision making (GPT-5)
response = client.responses.create(
    model="gpt-5",
    input="Evaluate this profile: ...",
    text={"verbosity": "low"},  # Nested!
    reasoning={"effort": "minimal"},  # For speed
    max_output_tokens=4000,  # Not 800!
    temperature=0.7
)

# For Computer Use
cua_response = client.responses.create(
    model="computer-use-preview",
    input="Click submit button",
    tools=[{
        "type": "computer_use_preview",
        "display_width": 1280,
        "display_height": 800
    }],
    truncation="auto",
    previous_response_id=prev_id if prev_id else None
)
```

---

END OF CONTEXT7 TRUTH - USE THIS AS REFERENCE