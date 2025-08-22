# AUDIT AND PLAN - Model Resolution & Flow Analysis
*Date: August 21, 2025*

## 🔍 CURRENT STATE AUDIT

### 1. How Models Are Currently Set

#### Decision Model (NLP)
- **Current**: Hardcoded in `.env` as `OPENAI_DECISION_MODEL=gpt-5-thinking`
- **Problem**: We're hardcoding a model ID that might not exist on the account
- **Used in**: `src/yc_matcher/infrastructure/openai_decision.py:30`

#### Computer Use Model
- **Current**: Hardcoded in `.env` as `CUA_MODEL=computer-use-preview`
- **Used in**: `src/yc_matcher/infrastructure/openai_cua_browser.py`

### 2. The ACTUAL 3-Input Flow

#### What We Have (CORRECT):
```
1. User provides: Profile + Criteria + Template
2. Criteria and Template are combined into one text block
3. Sent to NLP model (currently hardcoded gpt-5-thinking)
4. NLP returns: {decision, rationale, draft}
5. If YES: Playwright/CUA pastes draft and sends
```

#### Code Evidence:
```python
# openai_decision.py lines 61-88
# Template IS extracted from criteria and sent to NLP!
if "\nMessage Template:" in criteria.text:
    parts = criteria.text.split("\nMessage Template:")
    criteria_text = parts[0]
    template = parts[1].strip()
    
if template:
    user_text += f"MESSAGE TEMPLATE (use this style but personalize it):\n{template}\n\n"
```

**✅ This is CORRECT - Template goes to NLP for personalization**

### 3. Model Discovery Status

#### What We Have:
- `check_cua.py` DOES use `models.list()` to discover available models
- But main app DOESN'T - it just reads from env var

#### What SSOT Says:
- Query Models API at runtime
- Pick best GPT-5* available
- Don't hardcode IDs

**❌ We're NOT following SSOT - we're hardcoding**

## 📊 GAP ANALYSIS

### What's Working:
1. ✅ 3-input flow is correct (template goes to NLP)
2. ✅ Decision engine returns proper JSON structure
3. ✅ Computer Use and Decision are separate APIs
4. ✅ Playwright executes actions for CUA

### What's NOT Following SSOT:
1. ❌ Hardcoded model IDs instead of runtime discovery
2. ❌ No fallback if gpt-5-thinking doesn't exist
3. ❌ No model_selected event logging
4. ❌ No verification that chosen model exists

## 🎯 REFACTORING PLAN

### Priority 1: Model Resolution (CRITICAL)

Create `src/yc_matcher/infrastructure/model_resolver.py`:
```python
from openai import OpenAI
import os
import re
from typing import Optional

def resolve_best_decision_model(client: OpenAI) -> str:
    """Discover best GPT-5 model via Models API."""
    models = client.models.list()
    ids = [m.id for m in models.data]
    
    # 1. Try GPT-5 thinking variants
    gpt5_thinking = [m for m in ids if 'gpt-5' in m.lower() and 'thinking' in m.lower()]
    if gpt5_thinking:
        return sorted(gpt5_thinking, reverse=True)[0]
    
    # 2. Try any GPT-5
    gpt5_any = [m for m in ids if m.lower().startswith('gpt-5')]
    if gpt5_any:
        return sorted(gpt5_any, reverse=True)[0]
    
    # 3. Fallback to GPT-4 variants (despite user preference)
    gpt4_variants = [m for m in ids if m.lower().startswith('gpt-4')]
    if gpt4_variants:
        # Sort to get newest (4o, 4.1, etc)
        return sorted(gpt4_variants, reverse=True)[0]
    
    raise RuntimeError("No suitable GPT model found. Check API key and tier.")

def resolve_cua_model(client: OpenAI) -> Optional[str]:
    """Discover Computer Use model if available."""
    models = client.models.list()
    ids = [m.id for m in models.data]
    
    # Look for computer-use variants
    cua_models = [m for m in ids if 'computer' in m.lower() or 'cua' in m.lower()]
    if cua_models:
        return cua_models[0]
    
    return None
```

### Priority 2: Wire Resolution at Startup

In `build_services()` or app startup:
```python
from openai import OpenAI
from .model_resolver import resolve_best_decision_model, resolve_cua_model

client = OpenAI()

# Resolve models once at startup
decision_model = resolve_best_decision_model(client)
cua_model = resolve_cua_model(client)

# Log what we're using
logger.emit({
    "event": "models_resolved",
    "decision_model": decision_model,
    "cua_model": cua_model or "none"
})

# Set for use
os.environ["DECISION_MODEL_RESOLVED"] = decision_model
if cua_model:
    os.environ["CUA_MODEL_RESOLVED"] = cua_model
```

### Priority 3: Update Decision Adapter

Change `openai_decision.py`:
```python
def __init__(self, ...):
    # Use resolved model, not hardcoded
    self.model = model or os.getenv("DECISION_MODEL_RESOLVED") or os.getenv("OPENAI_DECISION_MODEL")
```

## ✅ WHAT'S ALREADY CORRECT

1. **Template Flow**: Template IS sent to NLP (good!)
2. **Separation**: CUA and Decision are separate APIs (good!)
3. **Execution**: Playwright executes for CUA (good!)
4. **JSON Response**: Decision returns proper structure (good!)

## ⚠️ WHAT TO KEEP AS-IS

1. **The 3-input flow** - Don't change, it's working correctly
2. **Template personalization** - NLP is already doing this right
3. **CUA/Playwright relationship** - They work together properly

## 🚫 WHAT NOT TO DO

1. **Don't remove GPT-4 fallbacks** - Account might not have GPT-5
2. **Don't hardcode ANY model IDs** - Use Models API
3. **Don't change the template flow** - It's correct

## 📋 IMPLEMENTATION CHECKLIST

- [ ] Create model_resolver.py with discovery functions
- [ ] Wire resolver in startup/DI
- [ ] Update decision adapter to use resolved model
- [ ] Update CUA to use resolved model
- [ ] Add model_selected event logging
- [ ] Test with account that has GPT-5
- [ ] Test with account that doesn't have GPT-5
- [ ] Document fallback behavior

## 🎬 FINAL STATE

When complete:
1. Models discovered at runtime via Models API
2. Best available model auto-selected (GPT-5 preferred)
3. Graceful fallback if GPT-5 unavailable
4. Clear logging of what models are being used
5. No hardcoded model IDs anywhere

---

**This audit confirms: The flow is correct, but model resolution needs fixing.**