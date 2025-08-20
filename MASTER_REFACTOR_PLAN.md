# MASTER Refactoring Plan - Based on ACTUAL Codebase

## Executive Summary

After deep audit of the ACTUAL codebase, we found:
- **80% of code already exists and works**
- **CUA is implemented but uses wrong API** (Agents SDK vs Responses API)
- **Decision modes exist but aren't labeled/configurable**
- **Only need to modify 4 files and create 1 new file**

## Files to Modify (NOT Create from Scratch)

### 1. Fix CUA Implementation (Must Include Playwright!)
**File**: `src/yc_matcher/infrastructure/openai_cua_browser.py`
- **Current**: Uses Agents SDK (wrong) and missing Playwright integration
- **Fix**: Use Responses API + integrate Playwright for execution
- **Critical**: CUA analyzes screenshots, Playwright executes actions (they work TOGETHER)
- **Effort**: 3-4 hours
- **Details**: [REAL_REFACTOR_SECTION_1_CUA.md](./REAL_REFACTOR_SECTION_1_CUA.md)

### 2. Add 3-Input UI Mode
**File**: `src/yc_matcher/interface/web/ui_streamlit.py`
- **Current**: Paste-based UI
- **Fix**: Add 3-input mode behind feature flag
- **Effort**: 2 hours
- **Details**: [REAL_REFACTOR_SECTION_2_UI.md](./REAL_REFACTOR_SECTION_2_UI.md)

### 3. Wire Decision Modes
**File**: `src/yc_matcher/interface/di.py`
- **Current**: Has all components but no mode selection
- **Fix**: Add mode selector function
- **Effort**: 1.5 hours
- **Details**: [REAL_REFACTOR_SECTION_5_DI.md](./REAL_REFACTOR_SECTION_5_DI.md)

### 4. Fix CUA Check
**File**: `src/yc_matcher/interface/cli/check_cua.py`
- **Current**: Checks for Agents SDK
- **Fix**: Check for Responses API
- **Effort**: 30 minutes
- **Details**: Minor update

## New File to Create (Only 1!)

### Autonomous Flow
**File**: `src/yc_matcher/application/autonomous_flow.py`
- **Purpose**: CUA-driven autonomous browsing
- **Reuses**: All existing use cases and infrastructure
- **Effort**: 2-3 hours
- **Details**: [REAL_REFACTOR_SECTION_4_USE_CASES.md](./REAL_REFACTOR_SECTION_4_USE_CASES.md)

## Tests to Add

### Critical Missing Tests:
1. `tests/unit/test_openai_cua_browser.py` - CUA implementation
2. `tests/unit/test_ui_streamlit.py` - UI components
3. `tests/integration/test_autonomous_flow.py` - Full flow
4. `tests/unit/test_di.py` - DI configuration
5. `tests/unit/test_decision_modes.py` - Mode behaviors

**Details**: [REAL_REFACTOR_SECTION_6_TESTS.md](./REAL_REFACTOR_SECTION_6_TESTS.md)

## Decision Modes Already Exist!

| Mode | Current Implementation | Just Need To |
|------|----------------------|--------------|
| Advisor | `OpenAIDecisionAdapter` | Add label + no-auto-send flag |
| Rubric | `WeightedScoringService` | Wrap in thin adapter |
| Hybrid | `GatedDecision` | Add configuration |

**Details**: [REAL_REFACTOR_SECTION_3_DECISIONS.md](./REAL_REFACTOR_SECTION_3_DECISIONS.md)

## Implementation Order

### Day 1 Morning: Fix CUA API (3 hrs)
1. Update `openai_cua_browser.py` to use Responses API
2. Add test `test_openai_cua_browser.py`
3. Verify with `make test`

### Day 1 Afternoon: Add UI Mode (2 hrs)
1. Add 3-input mode to `ui_streamlit.py`
2. Keep behind `USE_THREE_INPUT_UI` flag
3. Add test `test_ui_streamlit.py`

### Day 2 Morning: Create Autonomous Flow (3 hrs)
1. Create `autonomous_flow.py`
2. Wire into DI
3. Add integration tests

### Day 2 Afternoon: Wire Everything (2 hrs)
1. Update `di.py` for mode selection
2. Test end-to-end
3. Document usage

## Environment Variables

### Already Used:
- `ENABLE_CUA=1` - Enable CUA browser
- `ENABLE_OPENAI=1` - Enable OpenAI decisions
- `ENABLE_PLAYWRIGHT=1` - Enable Playwright
- `CUA_MODEL` - CUA model name
- `OPENAI_DECISION_MODEL` - Decision model

### To Add:
- `USE_THREE_INPUT_UI=true` - Enable new UI
- `DECISION_MODE=hybrid` - Select mode
- `AUTO_BROWSE_LIMIT=20` - Max profiles

## Migration Strategy

```bash
# Phase 1: Deploy with everything off
USE_THREE_INPUT_UI=false
ENABLE_CUA=false

# Phase 2: Test CUA with fixed API
ENABLE_CUA=true
ENABLE_PLAYWRIGHT_FALLBACK=true

# Phase 3: Enable new UI for testing
USE_THREE_INPUT_UI=true

# Phase 4: Full production
DECISION_MODE=hybrid
AUTO_BROWSE=true
```

## What We're NOT Doing

❌ NOT creating new browser implementations (PlaywrightBrowser exists)
❌ NOT creating new decision adapters (OpenAI/Local exist)
❌ NOT rewriting infrastructure (quotas, logging work)
❌ NOT creating duplicate UI files
❌ NOT touching working components

## Success Metrics

- [ ] CUA uses Responses API with `truncation="auto"`
- [ ] 3-input UI mode available
- [ ] Decision modes selectable
- [ ] Autonomous flow works end-to-end
- [ ] All tests pass
- [ ] Feature flags protect changes

## Total Effort

- **Files to modify**: 4
- **Files to create**: 1
- **Tests to add**: 5
- **Total LOC changed**: ~500
- **Total time**: 10-12 hours
- **Risk**: LOW (feature flags)

## Conclusion

This is NOT a massive refactor. The codebase is well-structured and mostly complete. We just need to:
1. Fix the CUA API (Agents → Responses)
2. Add 3-input UI mode
3. Create autonomous flow
4. Wire up mode selection

The original 4-part refactor docs assumed building from scratch. The reality is we're making targeted fixes to an existing, working system.