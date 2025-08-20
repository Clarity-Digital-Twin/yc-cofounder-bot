# ACTUAL Refactoring Targets - Based on Real Codebase Audit

## ⚠️ CRITICAL DISCOVERY

**The codebase ALREADY HAS CUA implementation!** But it uses the WRONG API (Agents SDK instead of Responses API).

## 🎯 FILES TO MODIFY (Not Create!)

### 1. Fix CUA Implementation (MODIFY EXISTING)

**File**: `src/yc_matcher/infrastructure/openai_cua_browser.py` ✅ EXISTS
- **Current**: Uses Agents SDK (`from agents import Agent, ComputerTool`)
- **Change To**: Responses API (`client.responses.create()`)
- **Keep**: Same BrowserPort interface methods

```python
# CURRENT (WRONG):
from agents import Agent, ComputerTool, Session
agent = Agent(model=os.getenv("CUA_MODEL"), tools=[ComputerTool()])

# CHANGE TO (RIGHT):
from openai import OpenAI
client = OpenAI()
response = client.responses.create(
    model=os.getenv("CUA_MODEL"),
    tools=[{"type": "computer_use_preview", ...}],
    truncation="auto"
)
```

### 2. Update Streamlit UI (MODIFY EXISTING)

**File**: `src/yc_matcher/interface/web/ui_streamlit.py` ✅ EXISTS
- **Current**: Single paste text area
- **Add**: 3-input mode (Your Profile, Criteria, Template)
- **Keep**: Existing paste mode behind feature flag

```python
# Add to existing file:
if os.getenv("USE_THREE_INPUT_UI") == "true":
    render_three_input_panel()  # NEW
else:
    render_paste_panel()  # EXISTING
```

### 3. Fix CUA Check Utility (MODIFY EXISTING)

**File**: `src/yc_matcher/interface/cli/check_cua.py` ✅ EXISTS
- **Current**: Checks for Agents SDK
- **Change To**: Check for Responses API capability
- **Keep**: Same validation flow

### 4. Enhance DI Configuration (MODIFY EXISTING)

**File**: `src/yc_matcher/interface/di.py` ✅ EXISTS
- **Current**: Has CUA support with `ENABLE_CUA=1`
- **Add**: Decision mode selection logic
- **Keep**: Existing browser selection

### 5. Create ONE New File for Autonomous Flow

**NEW File**: `src/yc_matcher/application/autonomous_flow.py` ❌ DOESN'T EXIST
- **Purpose**: CUA-driven autonomous browsing
- **Why New**: Current `use_cases.py` is paste-based
- **Integration**: Reuse existing components

## 🚫 FILES WE DON'T NEED TO CREATE

These already exist and work fine:

1. ✅ `src/yc_matcher/infrastructure/browser_playwright.py` - Fallback browser
2. ✅ `src/yc_matcher/infrastructure/openai_decision.py` - AI decisions
3. ✅ `src/yc_matcher/infrastructure/local_decision.py` - Basic decisions
4. ✅ `src/yc_matcher/application/gating.py` - Hybrid mode (gated decisions)
5. ✅ `src/yc_matcher/domain/services.py` - Scoring services
6. ✅ All quota, logging, storage infrastructure

## 📝 Decision Modes Already Exist!

**Advisor Mode**: `openai_decision.py` (AI-only)
**Rubric Mode**: `services.py` + `gating.py` (scoring)
**Hybrid Mode**: `gating.py` (threshold + AI)

Just need to:
- Add labels/configuration
- Add auto-send rules
- Wire up mode selection in DI

## 🧪 Tests to ADD (Not Modify)

### Critical Missing Tests:
1. `tests/unit/test_openai_cua_browser.py` - For CUA implementation
2. `tests/unit/test_ui_streamlit.py` - For UI components
3. `tests/integration/test_autonomous_flow.py` - For new flow
4. `tests/integration/test_cua_fallback.py` - For CUA→Playwright fallback

### Already Well Tested:
- ✅ Decision logic
- ✅ Scoring services
- ✅ Quota management
- ✅ Stop flag
- ✅ Playwright browser

## 🔄 Refactoring Strategy

### Phase 1: Fix CUA API (1 file)
1. Modify `openai_cua_browser.py` to use Responses API
2. Add test `test_openai_cua_browser.py`

### Phase 2: Add 3-Input UI (1 file)
1. Modify `ui_streamlit.py` to add 3-input mode
2. Keep paste mode as fallback
3. Add test `test_ui_streamlit.py`

### Phase 3: Create Autonomous Flow (1 new file)
1. Create `autonomous_flow.py` 
2. Wire into existing DI
3. Add integration tests

### Phase 4: Label Decision Modes (0 new files)
1. Update `di.py` to select modes
2. Add configuration for auto-send rules
3. Use existing decision implementations

## ⚠️ AVOID THESE MISTAKES

❌ DON'T create new decision adapter files (they exist!)
❌ DON'T create new browser files (PlaywrightBrowser exists!)
❌ DON'T duplicate existing infrastructure (quotas, logging work!)
❌ DON'T create parallel UI files (modify existing Streamlit!)

## 📊 Summary

- **Files to Modify**: 4 existing files
- **Files to Create**: 1 new file (autonomous_flow.py)
- **Tests to Add**: 4 test files
- **Lines to Change**: ~500-700 (mostly in CUA browser)
- **Risk Level**: LOW (feature flags protect changes)

The codebase is 80% ready. We just need to:
1. Fix the CUA API implementation
2. Add 3-input UI mode
3. Create autonomous flow
4. Wire up decision mode selection

NO MASSIVE REWRITE NEEDED!