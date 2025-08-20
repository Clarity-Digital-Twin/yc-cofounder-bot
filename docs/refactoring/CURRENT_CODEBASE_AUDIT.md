# Current Codebase Audit - YC Cofounder Bot

## Executive Summary

The codebase implements a **paste-based evaluation workflow** instead of the documented **3-input autonomous CUA flow**. While the architecture is clean and CUA integration exists, the fundamental user flow is backwards from documentation.

## Critical Misalignments

### 1. User Flow: Paste vs 3-Input

**CURRENT (Wrong)**:
```python
# src/yc_matcher/interface/web/ui_streamlit.py
profile_text = st.text_area("Paste candidate profile here")
if st.button("Evaluate"):
    decision = evaluate(profile_text)
```

**DOCUMENTED (Expected)**:
```python
# Should be:
your_profile = st.text_area("Your Profile")
match_criteria = st.text_area("Match Criteria")  
message_template = st.text_area("Message Template")
if st.button("Start Autonomous Browsing"):
    cua.browse_and_match(url, your_profile, criteria, template)
```

### 2. CUA Integration: Secondary vs Primary

**CURRENT**: CUA is an optional fallback for message sending
**DOCUMENTED**: CUA should drive the entire browsing/extraction flow

### 3. Decision Flow: Single vs Multi-Mode

**CURRENT**: One decision path with OpenAI or Local adapter
**DOCUMENTED**: Three modes - Advisor, Rubric, Hybrid

## Architecture Analysis

### Clean Architecture ✅
```
src/yc_matcher/
├── domain/          # Entities, value objects, services
├── application/     # Use cases, ports
├── infrastructure/  # Adapters (OpenAI, browser, storage)
└── interface/      # UI (Streamlit, CLI)
```

### Domain Layer
- **Entities**: `Profile`, `Criteria`, `Score`, `Decision`
- **Services**: `WeightedScoringService`, `GatedDecision`
- **Good**: Clean business logic separation
- **Bad**: Missing decision mode abstractions

### Application Layer
- **Use Cases**: `ProcessCandidate` - handles evaluation workflow
- **Ports**: `BrowserPort`, `DecisionPort`, `QuotaPort`
- **Good**: Proper dependency injection
- **Bad**: Use case assumes paste workflow

### Infrastructure Layer
- **OpenAI**: Two adapters - `OpenAIDecisionAdapter`, `OpenAICUABrowser`
- **Browser**: `PlaywrightBrowser` for DOM automation
- **Storage**: SQLite for quotas, progress, dedup
- **Good**: CUA adapter exists!
- **Bad**: CUA not integrated into main flow

### Interface Layer
- **Web**: Streamlit with paste-based UI
- **CLI**: Basic evaluation runner
- **Good**: Clean separation
- **Bad**: Wrong UI paradigm

## File-by-File Critical Issues

### 1. `ui_streamlit.py` - Complete Rewrite Needed
- Shows paste text area instead of 3 inputs
- No CUA browsing initiation
- No decision mode selector

### 2. `ProcessCandidate` Use Case - Major Refactor
- Expects pasted text, not URL
- No CUA browsing integration
- Single decision path

### 3. `OpenAICUABrowser` - Underutilized
- Exists but not called from main flow
- Only used for message sending
- Should drive entire process

### 4. Missing Decision Modes
- No `AdvisorMode` class
- No `RubricMode` class
- No `HybridMode` class
- Only `OpenAIDecisionAdapter` and `LocalDecisionAdapter`

## What's Working Correctly

### Safety Features ✅
- STOP flag for emergency abort
- Quota management (daily/weekly)
- Deduplication tracking
- Message validation

### CUA Implementation (To be refactored)
```python
# src/yc_matcher/infrastructure/openai_cua_browser.py
class OpenAICUABrowser:
    def __init__(self):
        self.model = os.getenv("CUA_MODEL")  # Correct
        # NOTE: Prefer Responses API for Computer Use (planner) + Playwright (executor)
        # Agents Runner is optional; migrate to Responses API loop per SSOT
```

### Dependency Injection ✅
```python
# src/yc_matcher/interface/di.py
def create_browser() -> BrowserPort:
    if os.getenv("ENABLE_CUA") == "1":
        return OpenAICUABrowser()  # CUA prioritized
    elif os.getenv("ENABLE_PLAYWRIGHT") == "1":
        return PlaywrightBrowser()
    return NullBrowser()
```

## Code Statistics

- **Total Python Files**: 31
- **Lines of Code**: ~2,500
- **Test Files**: 18
- **Test Coverage**: ~60% (core logic only)

## Risk Assessment

### High Risk Items
1. **UI Complete Rewrite**: Streamlit needs total replacement
2. **Use Case Refactor**: ProcessCandidate needs CUA integration
3. **Missing Decision Modes**: Need 3 new mode implementations

### Medium Risk Items
1. **Test Suite**: No CUA tests exist
2. **Integration Points**: Browser port needs expansion
3. **Configuration**: Missing decision mode settings

### Low Risk Items
1. **Domain Models**: Can mostly be reused
2. **Safety Features**: Already working well
3. **Logging**: Comprehensive and functional

## Recommendations

### Must Fix Immediately
1. Create 3-input UI panel
2. Integrate CUA into main flow
3. Implement decision modes

### Should Fix Soon
1. Add CUA test coverage
2. Update use cases for autonomous flow
3. Add decision mode configuration

### Nice to Have
1. Performance optimizations
2. Advanced rubric builder
3. Analytics dashboard

## Conclusion

The codebase has good bones but implements the wrong product. The architecture supports the needed changes, but requires significant refactoring of the application and interface layers. The CUA integration exists but needs to become the primary driver rather than a fallback option.
