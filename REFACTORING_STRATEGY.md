# Professional Refactoring Strategy

## Overview

This document outlines how professional engineers would approach refactoring the YC Cofounder Bot from its current manual-paste implementation to the documented autonomous CUA-driven system. We'll use Test-Driven Development (TDD), incremental migration, and feature flags to maintain stability while transforming the core workflow.

## Refactoring Philosophy

### Why NOT Big Bang Rewrite
Professional teams avoid "rewrite from scratch" because:
- Risk of introducing new bugs
- Loss of accumulated bug fixes
- Inability to ship during rewrite
- No rollback path if things go wrong

### Strangler Fig Pattern
We'll use the Strangler Fig pattern:
1. Build new functionality alongside old
2. Gradually route traffic to new system
3. Remove old code once new is proven
4. Always maintain working state

## TDD Approach

### Test-First Development Cycle
```
1. Write failing test for new behavior
2. Write minimal code to pass test
3. Refactor while keeping tests green
4. Repeat
```

### Test Strategy Layers

#### 1. Contract Tests (New)
Define the CUA browser contract first:
```python
# tests/contracts/test_cua_browser_contract.py
class TestCUABrowserContract:
    def test_navigates_to_url(self, cua_browser):
        # Define expected behavior
        cua_browser.navigate("https://example.com")
        assert cua_browser.current_url == "https://example.com"
    
    def test_extracts_profile_data(self, cua_browser):
        # Define extraction contract
        profile = cua_browser.extract_profile()
        assert "name" in profile
        assert "skills" in profile
```

#### 2. Integration Tests (Adapt)
Modify existing to support both flows:
```python
# tests/integration/test_dual_flow.py
@pytest.mark.parametrize("flow_type", ["manual", "cua"])
def test_process_candidate_flow(flow_type):
    # Test both old and new flows
    if flow_type == "cua":
        browser = CUABrowserAdapter()
    else:
        browser = PlaywrightBrowser()
    # ... rest of test
```

#### 3. Unit Tests (Preserve)
Keep existing unit tests, add new ones:
- Existing tests validate shared logic
- New tests for CUA-specific components
- Mock boundaries between old/new

## Incremental Migration Plan

### Phase 1: Parallel Infrastructure (Week 1)

**Goal:** Add CUA without breaking existing flow

1. **Create New Port**
```python
# application/ports.py
class CUABrowserPort(Protocol):
    def start_session(self, url: str) -> SessionId: ...
    def take_screenshot(self) -> bytes: ...
    def send_action(self, action: Action) -> Result: ...
    def extract_visible_text(self) -> str: ...
```

2. **Implement CUA Adapter**
```python
# infrastructure/openai_cua_browser.py
class OpenAICUABrowser:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("CUA_MODEL", "computer-use-preview")
    
    async def navigate_and_extract(self, url: str) -> Profile:
        # Use CUA to browse and extract
        pass
```

3. **Feature Flag System**
```python
# config.py
class FeatureFlags:
    USE_CUA_BROWSER = os.getenv("USE_CUA", "false") == "true"
    ENABLE_DECISION_MODES = os.getenv("DECISION_MODES", "false") == "true"
```

### Phase 2: Dual-Mode UI (Week 2)

**Goal:** Support both workflows in UI

1. **Conditional UI Rendering**
```python
# interface/web/ui_streamlit.py
if FeatureFlags.USE_CUA_BROWSER:
    show_three_input_panel()  # New CUA flow
else:
    show_paste_panel()  # Existing flow
```

2. **Gradual Rollout**
- Deploy with flag off (existing users unaffected)
- Enable for internal testing
- Gradual percentage rollout
- Full migration when stable

### Phase 3: Decision Modes (Week 3)

**Goal:** Implement three decision modes

1. **Decision Mode Factory**
```python
# application/decision_modes.py
class DecisionModeFactory:
    @staticmethod
    def create(mode: str) -> DecisionPort:
        if mode == "advisor":
            return AdvisorMode()  # LLM only
        elif mode == "rubric":
            return RubricMode()   # Deterministic
        elif mode == "hybrid":
            return HybridMode()   # Combined
        else:
            return LegacyMode()   # Current behavior
```

2. **Backward Compatibility**
- Legacy mode preserves current behavior
- New modes available via config
- Gradual migration of users

### Phase 4: Clean Up (Week 4)

**Goal:** Remove old code safely

1. **Metrics-Driven Removal**
```python
# Monitor usage before removing
if metrics.get("legacy_flow_usage_30d") == 0:
    remove_legacy_code()
```

2. **Deprecation Warnings**
```python
# Add warnings before removal
def paste_and_evaluate():
    warnings.warn(
        "Manual paste deprecated. Switching to CUA flow on 2025-02-01",
        DeprecationWarning
    )
```

## Feature Flag Implementation

### Safe Feature Toggling

```python
# infrastructure/feature_flags.py
class FeatureManager:
    def __init__(self):
        self.flags = {
            "cua_browser": self._check_env("USE_CUA"),
            "decision_modes": self._check_env("ENABLE_MODES"),
            "auto_send": self._check_env("AUTO_SEND"),
        }
    
    def is_enabled(self, feature: str) -> bool:
        return self.flags.get(feature, False)
    
    def run_with_fallback(self, feature: str, new_func, old_func):
        """Run new code with automatic fallback"""
        if self.is_enabled(feature):
            try:
                return new_func()
            except Exception as e:
                logger.error(f"Feature {feature} failed: {e}")
                return old_func()  # Automatic fallback
        return old_func()
```

## Avoiding Redundancy

### Shared Abstractions

1. **Unified Profile Model**
```python
# domain/entities.py
@dataclass
class Profile:
    """Works for both manual and CUA extraction"""
    raw_text: str
    structured_data: dict = field(default_factory=dict)
    source: Literal["manual", "cua"] = "manual"
```

2. **Adapter Pattern**
```python
# Both adapters implement same port
class PlaywrightBrowser(BrowserPort): ...  # Old
class OpenAICUABrowser(BrowserPort): ...   # New
```

3. **Composition Over Inheritance**
```python
# Reuse components, don't duplicate
class HybridDecisionMode:
    def __init__(self):
        self.rubric = RubricMode()
        self.advisor = AdvisorMode()
    
    def evaluate(self, profile, criteria):
        # Combine existing modes
        rubric_result = self.rubric.evaluate(profile, criteria)
        advisor_result = self.advisor.evaluate(profile, criteria)
        return self._combine(rubric_result, advisor_result)
```

## Risk Mitigation

### Rollback Strategy

1. **Feature Flags Enable Instant Rollback**
```bash
# If CUA fails in production
export USE_CUA=false
# System instantly reverts to old flow
```

2. **Database Compatibility**
```python
# Migrations that work both ways
class Migration:
    def up(self):
        # Add new column, don't remove old
        add_column("profiles", "cua_data", nullable=True)
    
    def down(self):
        # Can safely rollback
        remove_column("profiles", "cua_data")
```

3. **Monitoring & Alerts**
```python
# Track both flows
metrics.track("flow_type", "cua" if USE_CUA else "manual")
metrics.track("cua_errors", error_count)

# Alert on degradation
if error_rate > threshold:
    alerts.page_oncall("CUA error rate high")
    feature_flags.disable("cua_browser")  # Auto-disable
```

## Testing Strategy Details

### 1. TDD for New Components

```python
# Write test first
def test_cua_browser_extracts_profile():
    browser = MockCUABrowser()
    browser.set_page_content("<div>John Doe, Python Dev</div>")
    
    profile = browser.extract_profile()
    
    assert profile.name == "John Doe"
    assert "Python" in profile.skills
```

### 2. Integration Testing

```python
# Test old and new together
def test_gradual_migration():
    # 50% of requests use new flow
    results = []
    for i in range(100):
        if i % 2 == 0:
            result = process_with_cua()
        else:
            result = process_with_manual()
        results.append(result)
    
    # Both flows should work
    assert all(r.success for r in results)
```

### 3. Chaos Engineering

```python
# Test failure scenarios
def test_cua_failure_fallback():
    with mock.patch("openai.CUA.navigate", side_effect=Exception):
        result = process_candidate()
        # Should fallback to manual
        assert result.flow_used == "manual"
```

## Professional Best Practices

### 1. Code Review Process
- Every PR requires 2 approvals
- Changes to critical path need architecture review
- Feature flags reviewed by SRE team

### 2. Deployment Pipeline
```yaml
# .github/workflows/deploy.yml
stages:
  - test: Run full test suite
  - canary: Deploy to 5% of traffic
  - monitor: Watch metrics for 1 hour
  - rollout: Gradual increase to 100%
  - rollback: Automatic if errors spike
```

### 3. Documentation
- Update docs BEFORE writing code
- Architecture Decision Records (ADRs)
- Runbooks for operations

### 4. Communication
- Daily standups during refactor
- Weekly stakeholder updates
- Incident reports for any issues

## Timeline

### Week 1: Foundation
- Set up feature flags
- Create CUA browser adapter
- Write contract tests
- Deploy with flags off

### Week 2: Parallel Flows  
- Implement dual-mode UI
- Add metrics/monitoring
- Internal testing
- 5% canary rollout

### Week 3: Decision Modes
- Build three modes
- Integration testing
- 25% rollout
- Performance tuning

### Week 4: Migration
- 50% rollout
- Fix edge cases
- 100% rollout
- Deprecation notices

### Week 5: Cleanup
- Remove old code
- Update documentation
- Retrospective
- Plan next iteration

## Conclusion

Professional refactoring is about managing risk while delivering value. By using TDD, feature flags, and incremental migration, we can transform the system while maintaining stability. The key is never breaking the working system - always have a path forward AND a path back.