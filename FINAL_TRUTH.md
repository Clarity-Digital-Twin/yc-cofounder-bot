# FINAL TRUTH - Model Resolution & Implementation
*Last Updated: August 21, 2025*

## 🎯 THE ACTUAL TRUTH

### What the External Auditor Says (CORRECT):
1. **Don't hardcode model IDs** - Use Models API to discover
2. **GPT-5 exists** - But availability varies by account/tier
3. **Computer Use is Responses API** - Returns actions, you execute

### What We Currently Have:
1. **Hardcoded models** in .env (BAD)
2. **Correct 3-input flow** - Template goes to NLP (GOOD)
3. **Proper API separation** - CUA and Decision are separate (GOOD)

## 📋 THE CORRECT IMPLEMENTATION

### 1. Model Discovery (NOT Hardcoding)

```python
# At startup, discover available models
from openai import OpenAI

client = OpenAI()
models = client.models.list()
available = [m.id for m in models.data]

# Find best GPT-5 (prefer thinking variants)
gpt5_models = [m for m in available if 'gpt-5' in m.lower()]
if 'gpt-5-thinking' in available:
    DECISION_MODEL = 'gpt-5-thinking'
elif gpt5_models:
    DECISION_MODEL = gpt5_models[0]
else:
    # Fallback if no GPT-5 (despite user preference)
    DECISION_MODEL = 'gpt-4o'  # or whatever is available

# Find Computer Use model
cua_models = [m for m in available if 'computer' in m.lower()]
CUA_MODEL = cua_models[0] if cua_models else None
```

### 2. The 3-Input Flow (ALREADY CORRECT)

```
User Provides:
1. Your Profile
2. Match Criteria  
3. Message Template

Flow:
Profile + Criteria + Template → GPT-5 → {decision, rationale, draft} → Send
```

**This is working correctly! Template IS sent to NLP for personalization.**

### 3. API Usage (ALREADY CORRECT)

#### For Decisions (NLP):
```python
client.chat.completions.create(
    model=DECISION_MODEL,  # Discovered, not hardcoded
    messages=[...],
    response_format={"type": "json_object"}
)
```

#### For Computer Use (When Enabled):
```python
client.responses.create(
    model=CUA_MODEL,  # Discovered, not hardcoded
    tools=[{"type": "computer_use_preview", ...}],
    previous_response_id=...
)
```

## ⚠️ WHAT NEEDS FIXING

### Must Fix:
1. **Model discovery** - Stop hardcoding, use Models API
2. **Fallback logic** - Handle when GPT-5 isn't available
3. **Startup logging** - Log which models were selected

### Already Working (Don't Touch):
1. ✅ Template flow (goes to NLP)
2. ✅ API separation (CUA vs Decision)
3. ✅ JSON response structure
4. ✅ Playwright execution

## 🚫 MISCONCEPTIONS TO CLEAR UP

### WRONG: "Always use gpt-5-thinking"
**RIGHT**: Use best available GPT-5, discovered via Models API

### WRONG: "Never use GPT-4"
**RIGHT**: GPT-4 is acceptable fallback if account has no GPT-5

### WRONG: "Computer Use replaces Playwright"
**RIGHT**: Computer Use plans, Playwright executes

### WRONG: "Template bypasses NLP"
**RIGHT**: Template goes to NLP for personalization (current code is correct)

## 📊 IMPLEMENTATION PRIORITY

### Priority 1: Add Model Discovery
Create `model_resolver.py` that:
- Queries Models API
- Selects best available
- Logs selection
- Sets environment variables

### Priority 2: Update Adapters
- Decision adapter uses resolved model
- CUA adapter uses resolved model
- Remove hardcoded defaults

### Priority 3: Document Fallback Chain
```
1. Try: gpt-5-thinking
2. Try: any gpt-5*
3. Try: gpt-4o or gpt-4.1
4. Fail: No suitable model
```

## ✅ VALIDATION CHECKLIST

- [ ] Models discovered at runtime (not hardcoded)
- [ ] GPT-5 preferred but not required
- [ ] Template sent to NLP (already working)
- [ ] CUA and Decision use separate APIs (already working)
- [ ] Clear logging of model selection
- [ ] Graceful fallback when GPT-5 unavailable

## 🎬 END STATE

When this is implemented:
1. **No hardcoded model IDs anywhere**
2. **Best available model auto-selected**
3. **Clear fallback chain documented**
4. **Existing correct flows unchanged**

---

**Bottom Line: The flow is correct. We just need to stop hardcoding model IDs.**