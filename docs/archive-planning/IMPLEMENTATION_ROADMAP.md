# Implementation Roadmap: Manual to CUA Migration

## Project Overview

Transform YC Cofounder Bot from manual paste-and-evaluate to autonomous CUA-driven browser automation with three decision modes.

**Duration:** 5 weeks  
**Approach:** TDD with feature flags  
**Risk Level:** High (complete workflow reversal)  

## Pre-Implementation Checklist

- [ ] OpenAI API key with CUA access confirmed
- [ ] Stakeholder sign-off on breaking changes
- [ ] Backup of production database
- [ ] Rollback plan documented
- [ ] On-call schedule for migration period

## Week 1: Foundation Layer

### Day 1-2: CUA Integration Setup

**Task:** Create OpenAI CUA browser adapter

```python
# src/yc_matcher/infrastructure/openai_cua_browser.py
class OpenAICUABrowser:
    """Browser automation via OpenAI Computer-Using Agent"""
    
    async def start_session(self, url: str) -> Session
    async def take_screenshot(self) -> Screenshot
    async def perform_action(self, action: Action) -> Result
    async def extract_text(self) -> str
```

**Tests First:**
```python
# tests/unit/test_openai_cua_browser.py
- test_cua_browser_initialization
- test_screenshot_capture
- test_action_execution
- test_text_extraction
- test_error_handling
```

**Acceptance Criteria:**
- CUA client connects successfully
- Can capture screenshots
- Can execute basic navigation
- Error handling with retry logic

### Day 3-4: Feature Flag System

**Task:** Implement robust feature flagging

```python
# src/yc_matcher/infrastructure/feature_flags.py
class FeatureFlags:
    CUA_BROWSER = "cua_browser"
    DECISION_MODES = "decision_modes"
    AUTO_SEND = "auto_send"
    THREE_INPUT_UI = "three_input_ui"
```

**Configuration:**
```yaml
# config/features.yaml
features:
  cua_browser:
    enabled: false
    rollout_percentage: 0
    allowlist: ["test@example.com"]
  decision_modes:
    enabled: false
    available: ["advisor", "rubric", "hybrid"]
```

**Tests:**
- test_feature_flag_loading
- test_percentage_rollout
- test_allowlist_override
- test_fallback_behavior

### Day 5: Monitoring Infrastructure

**Task:** Set up metrics and logging

```python
# src/yc_matcher/infrastructure/metrics.py
class Metrics:
    def track_flow_type(flow: str)
    def track_cua_latency(ms: int)
    def track_error(error: Exception)
    def track_decision_mode(mode: str)
```

**Dashboards:**
- CUA success rate
- Latency comparison (manual vs CUA)
- Error rates by component
- Feature flag status

## Week 2: Parallel Implementation

### Day 1-2: CUA Port Definition

**Task:** Define new port interface

```python
# src/yc_matcher/application/ports.py
class CUAPort(Protocol):
    async def browse_to_profile(self, url: str) -> ProfileData
    async def evaluate_profile(self, criteria: Criteria) -> Decision
    async def send_message(self, message: str) -> bool
```

**Bridge Pattern:**
```python
# src/yc_matcher/application/browser_bridge.py
class BrowserBridge:
    def __init__(self, feature_flags: FeatureFlags):
        if feature_flags.is_enabled(FeatureFlags.CUA_BROWSER):
            self.impl = OpenAICUABrowser()
        else:
            self.impl = PlaywrightBrowser()
```

### Day 3-4: Dual-Mode Use Cases

**Task:** Modify use cases for both flows

```python
# src/yc_matcher/application/use_cases.py
class ProcessCandidateV2:
    def __init__(self, browser: BrowserPort, mode: str = "legacy"):
        self.browser = browser
        self.mode = mode
    
    def __call__(self, inputs: ProcessInputs) -> ProcessResult:
        if self.mode == "cua":
            return self._process_with_cua(inputs)
        else:
            return self._process_manual(inputs)
```

**Tests:**
```python
@pytest.mark.parametrize("mode", ["legacy", "cua"])
def test_process_candidate_modes(mode):
    # Test both paths
```

### Day 5: Integration Testing

**Task:** End-to-end flow validation

```python
# tests/integration/test_dual_flow.py
class TestDualFlow:
    def test_legacy_flow_unchanged(self)
    def test_cua_flow_works(self)
    def test_fallback_on_cua_error(self)
    def test_metrics_tracking(self)
```

## Week 3: Decision Modes

### Day 1-2: Mode Implementations

**Task:** Build three decision modes

```python
# src/yc_matcher/application/decision_modes/
├── advisor.py      # LLM-only evaluation
├── rubric.py       # Deterministic rules
└── hybrid.py       # Combined approach
```

**Advisor Mode:**
```python
class AdvisorMode:
    async def evaluate(self, profile: Profile, criteria: Criteria) -> Decision:
        # Pure LLM evaluation
        response = await self.llm.evaluate(profile, criteria)
        return Decision(
            should_message=response.recommendation,
            confidence=response.confidence,
            rationale=response.rationale
        )
```

**Rubric Mode:**
```python
class RubricMode:
    def evaluate(self, profile: Profile, criteria: Criteria) -> Decision:
        # Deterministic scoring
        score = self.calculate_score(profile, criteria)
        return Decision(
            should_message=score > self.threshold,
            confidence=1.0,
            rationale=f"Score: {score}"
        )
```

**Hybrid Mode:**
```python
class HybridMode:
    def evaluate(self, profile: Profile, criteria: Criteria) -> Decision:
        advisor = await self.advisor.evaluate(profile, criteria)
        rubric = self.rubric.evaluate(profile, criteria)
        return self.combine_decisions(advisor, rubric)
```

### Day 3-4: Mode Selection UI

**Task:** Add mode selector to UI

```python
# src/yc_matcher/interface/web/components/mode_selector.py
def render_mode_selector():
    mode = st.selectbox(
        "Decision Mode",
        ["advisor", "rubric", "hybrid"],
        help="Choose evaluation strategy"
    )
    
    if mode == "advisor":
        st.info("AI-only evaluation (no auto-send)")
    elif mode == "rubric":
        threshold = st.slider("Score threshold", 0, 10, 5)
    elif mode == "hybrid":
        weight = st.slider("AI weight", 0.0, 1.0, 0.5)
```

### Day 5: Mode Testing

**Task:** Comprehensive mode testing

```python
# tests/unit/test_decision_modes.py
class TestDecisionModes:
    def test_advisor_mode_llm_only(self)
    def test_rubric_mode_deterministic(self)
    def test_hybrid_mode_combines(self)
    def test_mode_factory_creation(self)
```

## Week 4: UI Migration

### Day 1-2: Three-Input Panel

**Task:** Build new UI components

```python
# src/yc_matcher/interface/web/ui_streamlit_v2.py
def render_three_input_panel():
    col1, col2, col3 = st.columns(3)
    
    with col1:
        url = st.text_input(
            "YC Profile URL",
            placeholder="https://startup.school/profile/..."
        )
    
    with col2:
        criteria = st.text_area(
            "Match Criteria",
            placeholder="Skills, location, interests..."
        )
    
    with col3:
        limits = render_limit_controls()
    
    if st.button("Start Autonomous Browsing"):
        launch_cua_session(url, criteria, limits)
```

### Day 3-4: Progressive UI Rollout

**Task:** Conditional UI rendering

```python
# src/yc_matcher/interface/web/ui_router.py
def render_ui():
    if feature_flags.is_enabled("three_input_ui"):
        if st.sidebar.toggle("Use Legacy UI"):
            render_legacy_ui()
        else:
            render_three_input_panel()
    else:
        render_legacy_ui()
        if st.sidebar.checkbox("Preview New UI"):
            with st.expander("New UI Preview"):
                render_three_input_panel()
```

### Day 5: UI Testing

**Task:** UI component testing

```python
# tests/ui/test_three_input_panel.py
def test_three_inputs_render()
def test_validation_rules()
def test_cua_launch_trigger()
def test_legacy_compatibility()
```

## Week 5: Production Rollout

### Day 1: Canary Deployment

**Steps:**
1. Deploy with all flags disabled
2. Enable for internal team (allowlist)
3. Monitor metrics for 24 hours
4. Fix any issues found

**Rollout Script:**
```bash
# scripts/canary_rollout.sh
#!/bin/bash
echo "Starting canary deployment..."
kubectl set env deployment/yc-bot USE_CUA=false
kubectl rollout status deployment/yc-bot
echo "Enabling for internal testing..."
kubectl set env deployment/yc-bot CUA_ALLOWLIST="team@company.com"
```

### Day 2: 10% Rollout

**Progressive Rollout:**
```python
# config/rollout.py
ROLLOUT_SCHEDULE = {
    "2025-02-15 09:00": 0.10,  # 10%
    "2025-02-15 14:00": 0.25,  # 25% if metrics good
    "2025-02-16 09:00": 0.50,  # 50% next day
    "2025-02-17 09:00": 1.00,  # 100% if stable
}
```

### Day 3: Issue Resolution

**Common Issues to Watch:**
- CUA timeout on slow pages
- Screenshot size limits
- Rate limiting from OpenAI
- User confusion with new UI

**Runbook:**
```markdown
## CUA Timeout Issue
1. Check OpenAI API status
2. Increase timeout to 30s
3. Add retry with exponential backoff
4. If persists, disable CUA flag

## High Error Rate
1. Check error logs for pattern
2. Identify affected users
3. Rollback if >5% error rate
4. Create hotfix PR
```

### Day 4: Full Rollout

**Final Steps:**
1. Enable all features at 100%
2. Monitor for 24 hours
3. Remove feature flags (make permanent)
4. Archive old code (don't delete yet)

### Day 5: Cleanup & Retrospective

**Cleanup Tasks:**
- Remove legacy UI code
- Delete old test files
- Update all documentation
- Remove feature flags
- Archive migration scripts

**Retrospective Questions:**
- What went well?
- What was challenging?
- What would we do differently?
- What did we learn?

## Post-Implementation

### Week 6+: Optimization

**Performance Tuning:**
- CUA action batching
- Screenshot compression
- Response caching
- Parallel evaluations

**Feature Enhancements:**
- Advanced rubric builder
- A/B testing framework
- Custom decision modes
- Analytics dashboard

## Success Metrics

### Technical Metrics
- [ ] CUA success rate >95%
- [ ] Latency <5s per profile
- [ ] Error rate <1%
- [ ] Test coverage >80%

### Business Metrics
- [ ] User adoption >75%
- [ ] Message send rate maintained
- [ ] No increase in complaints
- [ ] Positive user feedback

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|---------|------------|
| CUA API downtime | Medium | High | Fallback to manual mode |
| User resistance | High | Medium | Gradual rollout, education |
| Performance degradation | Low | High | Caching, optimization |
| Data loss | Low | Critical | Backups, gradual migration |
| Security breach | Low | Critical | Audit, penetration testing |

## Communication Plan

### Stakeholder Updates
- Daily: Engineering standup
- Weekly: Product team sync
- Bi-weekly: Executive briefing

### User Communication
- Week 1: "Coming soon" announcement
- Week 3: Beta testing invitation
- Week 5: Full launch announcement
- Week 6: Feedback survey

## Rollback Plan

If critical issues arise:

1. **Immediate:** Disable feature flags
```bash
export USE_CUA=false
export THREE_INPUT_UI=false
```

2. **Quick Fix:** Deploy hotfix within 4 hours

3. **Full Rollback:** Restore previous version
```bash
kubectl rollout undo deployment/yc-bot
```

4. **Data Recovery:** Restore from backups if needed

## Conclusion

This roadmap provides a safe, incremental path from manual to CUA-driven automation. By using TDD, feature flags, and careful monitoring, we minimize risk while transforming the core product. The key is maintaining a working system at every step while building the future architecture alongside it.