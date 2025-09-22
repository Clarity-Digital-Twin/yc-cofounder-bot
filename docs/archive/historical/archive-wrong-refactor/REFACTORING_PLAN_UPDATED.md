# UPDATED Refactoring Plan - Based on ACTUAL Codebase

## 🎉 Good News!

After deep audit, the codebase is **80% complete**! We have:
- ✅ CUA browser implementation (but wrong API)
- ✅ Playwright fallback browser
- ✅ Decision adapters (OpenAI + Local)
- ✅ Gated decisions (hybrid mode)
- ✅ Complete infrastructure (quotas, logging, storage)
- ✅ Dependency injection with CUA support

## 🔧 What Actually Needs Fixing

### 1. CUA Uses Wrong API
- **File**: `src/yc_matcher/infrastructure/openai_cua_browser.py`
- **Problem**: Uses Agents SDK instead of Responses API
- **Fix**: Change ~100 lines to use correct API

### 2. UI is Paste-Based
- **File**: `src/yc_matcher/interface/web/ui_streamlit.py`
- **Problem**: Single text area for pasting
- **Fix**: Add 3-input mode (keep paste as fallback)

### 3. Missing Autonomous Flow
- **New File**: `src/yc_matcher/application/autonomous_flow.py`
- **Problem**: Current flow requires manual paste
- **Fix**: Create CUA-driven browsing use case

### 4. Decision Modes Not Labeled
- **Files**: Existing decision adapters
- **Problem**: Modes exist but not configurable
- **Fix**: Add labels and auto-send rules

## 📁 Files to MODIFY (Not Create)

```
MODIFY (4 files):
├── src/yc_matcher/infrastructure/openai_cua_browser.py  # Fix API
├── src/yc_matcher/interface/web/ui_streamlit.py        # Add 3-input
├── src/yc_matcher/interface/di.py                      # Mode selection
└── src/yc_matcher/interface/cli/check_cua.py           # Fix validation

CREATE (1 file):
└── src/yc_matcher/application/autonomous_flow.py       # New use case

ADD TESTS (4 files):
├── tests/unit/test_openai_cua_browser.py               # CUA tests
├── tests/unit/test_ui_streamlit.py                     # UI tests
├── tests/integration/test_autonomous_flow.py           # Flow tests
└── tests/integration/test_cua_fallback.py              # Fallback tests
```

## 🚀 Simplified Refactoring Steps

### Step 1: Fix CUA API (2 hours)
```python
# In openai_cua_browser.py, change:
from agents import Agent, ComputerTool  # OLD
# To:
from openai import OpenAI  # NEW
client.responses.create(...)  # Use Responses API
```

### Step 2: Add 3-Input UI (2 hours)
```python
# In ui_streamlit.py, add:
if os.getenv("USE_THREE_INPUT_UI"):
    col1, col2, col3 = st.columns(3)
    your_profile = col1.text_area("Your Profile")
    criteria = col2.text_area("Match Criteria")
    template = col3.text_area("Message Template")
else:
    # Keep existing paste UI
```

### Step 3: Create Autonomous Flow (3 hours)
```python
# New file: autonomous_flow.py
class AutonomousFlow:
    def run(self, your_profile, criteria, template):
        # 1. CUA browses to YC
        # 2. Extracts profiles
        # 3. Evaluates each
        # 4. Sends messages
```

### Step 4: Wire Decision Modes (1 hour)
```python
# In di.py, add:
mode = os.getenv("DECISION_MODE", "hybrid")
if mode == "advisor":
    return OpenAIDecisionAdapter()  # EXISTS
elif mode == "rubric":
    return GatedDecision(scoring_only=True)  # EXISTS
elif mode == "hybrid":
    return GatedDecision()  # EXISTS
```

## ⚠️ What NOT to Do

❌ **DON'T** create new browser implementations
❌ **DON'T** create new decision adapters
❌ **DON'T** rewrite existing infrastructure
❌ **DON'T** create duplicate UI files
❌ **DON'T** touch working components (quotas, logging)

## 📊 Actual Effort Estimate

- **Total Files to Modify**: 4
- **Total New Files**: 1
- **Total Test Files**: 4
- **Estimated LOC Changes**: ~500
- **Estimated Time**: 8-10 hours
- **Risk Level**: LOW (feature flags protect)

## 🎯 Success Criteria

1. CUA uses Responses API with `truncation="auto"`
2. 3-input UI mode available (paste mode retained)
3. Autonomous browsing works end-to-end
4. Decision modes configurable via environment
5. All tests pass

## 🔄 Migration Path

```bash
# Phase 1: Deploy with no changes visible
USE_THREE_INPUT_UI=false
ENABLE_CUA=false

# Phase 2: Test CUA with fixed API
ENABLE_CUA=true
ENABLE_PLAYWRIGHT_FALLBACK=true

# Phase 3: Enable 3-input UI
USE_THREE_INPUT_UI=true

# Phase 4: Full autonomous mode
DECISION_MODE=hybrid
AUTO_BROWSE=true
```

## 📝 Next Steps

1. Read [ACTUAL_REFACTORING_TARGETS.md](./ACTUAL_REFACTORING_TARGETS.md) for detailed file list
2. Start with fixing `openai_cua_browser.py` (highest impact)
3. Add tests as you go (don't wait until end)
4. Use feature flags for safe rollout

The refactoring is MUCH simpler than originally thought. Most code exists and works - we just need to fix the CUA API and add the 3-input UI!
