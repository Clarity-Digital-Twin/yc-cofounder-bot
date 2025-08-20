# Section 3: Decision Systems

## Current Files:

### 1. `src/yc_matcher/infrastructure/openai_decision.py`
- **Lines**: ~90 lines
- **Purpose**: AI-based evaluation (Advisor mode)
- **Uses**: OpenAI API via `responses.create()`
- **Returns**: `{decision: YES/NO, rationale: string, draft: string}`
- **Model**: From `OPENAI_DECISION_MODEL` env var ✅

### 2. `src/yc_matcher/application/gating.py`
- **Lines**: ~25 lines
- **Purpose**: Threshold gating (Hybrid mode)
- **Logic**: Score first → if pass threshold → run AI decision
- **Threshold**: 4.0 (configurable)
- **Red flags**: -100.0 floor

### 3. `src/yc_matcher/infrastructure/local_decision.py`
- **Purpose**: Simple rule-based (placeholder)
- **Logic**: Always returns YES with basic name extraction

### 4. `src/yc_matcher/domain/services.py`
- **Has**: `WeightedScoringService` for keyword scoring
- **Weights**: Configurable per keyword

## What EXISTS (Mapped to Modes):

| Mode | Implementation | Auto-Send | Current Status |
|------|---------------|-----------|----------------|
| **Advisor** | `OpenAIDecisionAdapter` | No | ✅ EXISTS |
| **Rubric** | `WeightedScoringService` + threshold | Yes | ✅ EXISTS (in gating) |
| **Hybrid** | `GatedDecision` | Conditional | ✅ EXISTS |

## What's WRONG:
1. **NO MODE LABELS**: Can't select "advisor" vs "rubric" vs "hybrid"
2. **NO AUTO-SEND RULES**: Decision doesn't indicate if auto-send allowed
3. **NOT CONFIGURABLE**: Can't adjust weights/thresholds at runtime

## How to FIX:

```python
# In di.py, add mode selection:

def create_decision_adapter(mode: str = None):
    """Create decision adapter based on mode"""
    mode = mode or os.getenv("DECISION_MODE", "hybrid")
    
    if mode == "advisor":
        # Pure AI, no auto-send
        adapter = OpenAIDecisionAdapter(...)
        adapter.auto_send = False  # ADD this flag
        return adapter
        
    elif mode == "rubric":
        # Pure scoring, always auto-send
        scoring = WeightedScoringService(...)
        return RubricOnlyAdapter(scoring)  # Create thin wrapper
        
    elif mode == "hybrid":
        # Existing GatedDecision
        return GatedDecision(
            scoring=WeightedScoringService(...),
            decision=OpenAIDecisionAdapter(...),
            threshold=float(os.getenv("HYBRID_THRESHOLD", "4.0"))
        )

# Add thin wrapper for rubric mode:
class RubricOnlyAdapter(DecisionPort):
    def __init__(self, scoring: ScoringPort, threshold: float = 4.0):
        self.scoring = scoring
        self.threshold = threshold
        self.auto_send = True  # Always auto-send
        
    def evaluate(self, profile, criteria):
        score = self.scoring.score(profile, criteria)
        passed = score.value >= self.threshold
        return {
            "decision": "YES" if passed else "NO",
            "rationale": f"Score: {score.value:.1f}",
            "draft": "",  # No draft needed for rubric
            "mode": "rubric",
            "auto_send": self.auto_send
        }
```

## Test Coverage:
- `test_openai_decision_adapter.py` ✅ EXISTS
- `test_gated_decision.py` ✅ EXISTS  
- `test_scoring.py` ✅ EXISTS
- **Missing**: Mode selection tests

## Environment Variables to Add:
- `DECISION_MODE` = advisor|rubric|hybrid
- `HYBRID_THRESHOLD` = 4.0 (configurable)
- `RUBRIC_WEIGHTS` = JSON string of weights
- `AUTO_SEND_ADVISOR` = false (never)
- `AUTO_SEND_RUBRIC` = true (always)
- `AUTO_SEND_HYBRID_MIN_CONFIDENCE` = 0.7

## Effort Estimate:
- **Lines to add**: ~50 (mostly in di.py)
- **Time**: 1 hour
- **Risk**: Low (using existing components)
- **Testing**: Update existing tests