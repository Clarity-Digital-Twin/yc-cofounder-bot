# Section 5: Dependency Injection

## Current File: `src/yc_matcher/interface/di.py`

### What EXISTS Now:

#### Browser Selection (lines 100-117):
1. **PRIMARY**: Check `ENABLE_CUA=1` → Use OpenAICUABrowser
2. **FALLBACK**: If CUA fails + `ENABLE_PLAYWRIGHT_FALLBACK=1` → PlaywrightBrowser
3. **SECONDARY**: Check `ENABLE_PLAYWRIGHT=1` → PlaywrightBrowser
4. **NULL**: No browser enabled → NullBrowser

#### Decision Selection (lines 39-63):
1. **DEFAULT**: LocalDecisionAdapter (basic)
2. **IF `ENABLE_OPENAI=1`**: OpenAIDecisionAdapter
3. **ALWAYS**: Wrapped in GatedDecision for threshold checking

#### Other Services:
- **Scoring**: WeightedScoringService with default weights (line 33)
- **Logger**: JSONLLogger with stamps (lines 67-74)
- **Quota**: SQLite if calendar enabled, else file (line 84)
- **Template**: TemplateRenderer with banned phrases (line 41)

### What's WORKING:
- ✅ CUA browser already wired (line 101-104)
- ✅ Fallback logic exists
- ✅ OpenAI decision adapter wired
- ✅ Gated decision wrapping
- ✅ All infrastructure connected

### What's WRONG:
1. **NO MODE SELECTION**: Can't choose advisor/rubric/hybrid
2. **HARDCODED WEIGHTS**: Can't configure at runtime
3. **NO AUTONOMOUS FLOW**: Only returns ProcessCandidate components

### How to FIX:

```python
# ADD to existing file:

def create_decision_by_mode(
    mode: str = None,
    scoring: WeightedScoringService = None,
    threshold: float = 4.0
) -> DecisionPort:
    """Create decision adapter based on mode"""
    
    mode = mode or os.getenv("DECISION_MODE", "hybrid")
    
    if mode == "advisor":
        # Pure AI, no auto-send
        if os.getenv("ENABLE_OPENAI") == "1":
            from ..infrastructure.openai_decision import OpenAIDecisionAdapter
            client = _get_openai_client()  # Extract client creation
            adapter = OpenAIDecisionAdapter(client=client)
            adapter.auto_send = False  # Add flag
            return adapter
        else:
            return LocalDecisionAdapter()
            
    elif mode == "rubric":
        # Pure scoring, auto-send
        from ..application.rubric_only import RubricOnlyAdapter
        return RubricOnlyAdapter(scoring=scoring, threshold=threshold)
        
    elif mode == "hybrid":
        # Current GatedDecision
        base_decision = _get_base_decision()
        return GatedDecision(
            scoring=scoring,
            decision=base_decision,
            threshold=threshold
        )
    
    raise ValueError(f"Unknown mode: {mode}")

def build_autonomous_services(
    your_profile: str,
    criteria: str,
    template: str,
    mode: str = "hybrid"
) -> tuple[AutonomousFlow, LoggerWithStamps]:
    """Build services for autonomous flow"""
    
    # Get browser (CUA required for autonomous)
    if not os.getenv("ENABLE_CUA") == "1":
        raise RuntimeError("Autonomous flow requires ENABLE_CUA=1")
    
    from ..infrastructure.openai_cua_browser import OpenAICUABrowser
    from ..application.autonomous_flow import AutonomousFlow
    
    browser = OpenAICUABrowser()
    
    # Get decision by mode
    scoring = _get_scoring_service()
    decision = create_decision_by_mode(mode, scoring)
    
    # Reuse existing infrastructure
    eval_use, send_use, logger = build_services(
        criteria_text=criteria,
        template_text=template
    )
    
    # Build autonomous flow
    flow = AutonomousFlow(
        browser=browser,
        evaluate=eval_use,
        send=send_use,
        seen=_get_seen_repo(),
        logger=logger,
        stop=_get_stop_controller()
    )
    
    return flow, logger
```

### Test Coverage:
- **Current**: 0 tests ❌
- **Needed**: `tests/unit/test_di.py`

### Environment Variables:
Already used:
- `ENABLE_CUA` ✅
- `ENABLE_OPENAI` ✅
- `ENABLE_PLAYWRIGHT` ✅
- `ENABLE_PLAYWRIGHT_FALLBACK` ✅
- `ENABLE_CALENDAR_QUOTA` ✅

To add:
- `DECISION_MODE` = advisor|rubric|hybrid
- `SCORING_WEIGHTS` = JSON string
- `AUTO_SEND_CONFIG` = JSON config

### Effort Estimate:
- **Lines to add**: ~80
- **Time**: 1.5 hours
- **Risk**: Low (additive changes)
- **Testing**: Add DI tests