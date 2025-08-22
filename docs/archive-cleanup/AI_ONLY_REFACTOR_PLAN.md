# AI-Only Refactoring Plan

## Executive Summary
Simplify from 3 decision modes (advisor/rubric/hybrid) to a single AI-first mode that mirrors the actual workflow: paste profile → AI evaluates → get decision + draft message.

## Current State Analysis

### What We Have (Complexity to Remove)
1. **Three Decision Modes**:
   - `advisor`: AI-only, no auto-send
   - `rubric`: Rules-based scoring, auto-send
   - `hybrid`: Combines rubric gate + AI

2. **Unnecessary Abstractions**:
   - `RubricOnlyAdapter` (di.py:24-49)
   - `GatedDecision` (application/gating.py)
   - `WeightedScoringService` (domain/services.py)
   - Mode selection logic in `create_decision_adapter()` (di.py:52-129)

3. **UI Complexity**:
   - Mode selector dropdown (ui_streamlit.py:75-82)
   - Conditional threshold/alpha inputs (ui_streamlit.py:155-160)
   - Mode-specific logic throughout

4. **Test Overhead**:
   - `test_decision_modes.py` (230 lines of mode-specific tests)
   - `test_gated_decision.py` (gating logic tests)
   - `test_hybrid_draft.py` (hybrid mode tests)

### What We Want (Simple AI Pipeline)
1. **Single Decision Flow**:
   ```python
   OpenAIDecisionAdapter.evaluate(profile, criteria) 
   → {decision: "YES/NO", rationale: "...", draft: "...", score: 0.85}
   ```

2. **Clear Toggles**:
   - **Shadow Mode**: Evaluate only vs. Actually send
   - **Browser Mode**: Playwright vs. CUA planner
   - **Auto-Send**: Always require approval vs. Send if YES

## Refactoring Strategy (Professional TDD Approach)

### Phase 1: Write Tests First (RED)
```bash
# Create new test file
tests/unit/test_ai_only_decision.py
```

**Test Cases**:
1. `test_ai_decision_returns_structured_output()`
2. `test_ai_decision_includes_personalized_draft()`
3. `test_ai_decision_logs_usage_metrics()`
4. `test_ai_decision_handles_api_errors()`
5. `test_shadow_mode_prevents_sending()`

### Phase 2: Simplify DI Layer (GREEN)
**File: `src/yc_matcher/interface/di.py`**

```python
def build_services(...):
    # BEFORE: 130 lines of mode logic
    # AFTER: Direct AI adapter creation
    
    # 1. Remove RubricOnlyAdapter class (comment out lines 24-49)
    # 2. Remove create_decision_adapter factory (comment out lines 52-129)
    # 3. Direct instantiation:
    decision = OpenAIDecisionAdapter(
        client=OpenAI(),
        logger=logger,
        model=os.getenv("DECISION_MODEL_RESOLVED") or "gpt-4o"
    )
    
    # Keep all safety features
    eval_use = EvaluateProfile(decision=decision, message=renderer)
    send_use = SendMessage(quota=quota, browser=browser, logger=logger, stop=stop)
```

### Phase 3: Simplify UI (REFACTOR)
**File: `src/yc_matcher/interface/web/ui_streamlit.py`**

```python
# REMOVE:
# - Mode selector (lines 74-82)
# - Threshold input (lines 140-150)
# - Alpha input (lines 155-160)
# - Mode-specific logic (lines 310-311, 397)

# ADD:
st.checkbox("Shadow Mode (evaluate only, don't send)", key="shadow_mode")
st.checkbox("Auto-send on YES (skip manual approval)", key="auto_send")
```

### Phase 4: Clean Up Tests
**Comment out (don't delete yet)**:
- `tests/unit/test_decision_modes.py`
- `tests/unit/test_gated_decision.py`
- `tests/unit/test_hybrid_draft.py`
- Mode-specific assertions in integration tests

### Phase 5: Update Configuration
**File: `.env.example`**
```env
# REMOVE:
# DECISION_MODE=hybrid
# THRESHOLD=0.72
# ALPHA=0.50

# ADD:
AUTO_SEND=1                  # 0=require approval, 1=send on YES
SHADOW_MODE=0                # 0=live, 1=test only
```

## Implementation Checklist

### Code Changes (In Order)
- [ ] Write `test_ai_only_decision.py` with 5 core tests
- [ ] Comment out `RubricOnlyAdapter` class in di.py
- [ ] Comment out `create_decision_adapter()` factory in di.py
- [ ] Simplify `build_services()` to direct OpenAI adapter
- [ ] Remove mode selector from UI
- [ ] Remove threshold/alpha inputs from UI
- [ ] Add shadow_mode and auto_send checkboxes
- [ ] Update `.env.example` to remove mode configs
- [ ] Comment out old test files (don't delete)
- [ ] Run `make verify` - all tests should pass

### Documentation Updates
- [ ] Update README.md to show single AI mode
- [ ] Update SSOT.md to remove mode references
- [ ] Update CLAUDE.md guidance for AI-only
- [ ] Update docs/01-product-brief.md

### Validation
- [ ] Manual test: Start → evaluates with AI → shows decision
- [ ] Manual test: Shadow mode prevents sending
- [ ] Manual test: Auto-send works when enabled
- [ ] Check logs show clean decision events
- [ ] Verify no mode references in UI

## What We Keep (Important!)

### All Safety Features Stay
- ✅ STOP flag checking
- ✅ Quota limits (daily/weekly)
- ✅ Pacing between sends
- ✅ Deduplication (never message twice)
- ✅ Event logging (JSONL)
- ✅ Login preflight checks

### Browser Options Stay
- ✅ Playwright executor (always)
- ✅ CUA planner (optional via ENABLE_CUA)
- ✅ Single browser instance

### Core Flow Unchanged
```
Open YC → Loop profiles → Extract text → AI evaluate → 
(if YES & auto_send & !shadow) → Send → Verify → Next
```

## Migration Path

### For Existing Users
1. On update, default to:
   - `AUTO_SEND=0` (require approval like old advisor mode)
   - `SHADOW_MODE=0` (live mode)
2. Log warning if old DECISION_MODE env var detected
3. Map old modes to new behavior:
   - `advisor` → AUTO_SEND=0
   - `rubric/hybrid` → AUTO_SEND=1

### Rollback Plan
All old code is commented, not deleted. If issues:
1. Uncomment old code
2. Revert di.py changes
3. Re-enable mode selector in UI

## Code Metrics

### Lines Removed (Commented)
- RubricOnlyAdapter: 26 lines
- create_decision_adapter: 78 lines  
- GatedDecision: ~50 lines
- WeightedScoringService: ~40 lines
- Mode tests: ~400 lines
- **Total**: ~600 lines simplified

### New Code Added
- test_ai_only_decision.py: ~50 lines
- Simplified di.py: ~10 lines
- **Total**: ~60 lines added

### Net Reduction
**~540 lines removed** = cleaner, simpler, more maintainable

## Success Criteria
1. All tests pass (`make verify` green)
2. UI shows no mode selection
3. AI evaluation works end-to-end
4. Shadow mode prevents sends
5. Auto-send toggle works
6. Event logs are clean
7. No regression in safety features

## Timeline
- Phase 1-2: 30 minutes (core refactor)
- Phase 3-4: 20 minutes (UI cleanup)
- Phase 5: 10 minutes (config/docs)
- Testing: 30 minutes
- **Total**: 1.5 hours

## Notes
- This follows Uncle Bob's "Make it work, make it right, make it fast"
- We're at "make it right" - simplifying working code
- Comment don't delete - can remove in follow-up PR
- Tests first (TDD) ensures no regression
- Keep all safety features - they're orthogonal to decision logic