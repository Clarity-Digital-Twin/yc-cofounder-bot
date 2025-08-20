# Section 2: UI/Streamlit Implementation

## Current File: `src/yc_matcher/interface/web/ui_streamlit.py`

### What EXISTS Now:
- **Lines**: ~150 lines
- **Title**: "YC Co-Founder Matcher — Paste & Evaluate (Gated)"
- **Main Input**: Single text area for pasting profile (line 55)
- **Sidebar Settings**:
  - Criteria text area (line 24-29)
  - Message template (line 30-32)
  - Quota setting (line 33-35)
  - Shadow mode toggle (line 36)
  - STOP flag toggle (line 39-45)
- **Buttons**: 
  - "Evaluate" - Run decision
  - "Approve & Send (Playwright)" - Send if YES

### What's WRONG:
1. **PASTE-BASED**: Requires manual copy/paste of profiles
2. **NO 3-INPUT MODE**: Missing Your Profile, Criteria, Template as main inputs
3. **NO DECISION MODES**: No selector for Advisor/Rubric/Hybrid
4. **NO AUTONOMOUS**: No way to start CUA browsing

### How to FIX:

```python
# ADD to existing file (don't replace):

def render_three_input_mode():
    """New 3-input autonomous mode"""
    st.title("🚀 YC Co-Founder Matcher - Autonomous Mode")
    
    # Three main inputs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📝 Your Profile")
        your_profile = st.text_area(
            "Describe yourself",
            height=200,
            placeholder="Technical co-founder\n5 years Python/FastAPI\nNYC based",
            key="your_profile"
        )
    
    with col2:
        st.subheader("🎯 Match Criteria")
        criteria = st.text_area(
            "What you're looking for",
            height=200,
            placeholder="Business background\nB2B sales\nHealthcare experience",
            key="match_criteria"
        )
    
    with col3:
        st.subheader("💬 Message Template")
        template = st.text_area(
            "Outreach template",
            height=200,
            value=load_default_template(),
            key="msg_template"
        )
    
    # Decision mode selector
    st.markdown("---")
    mode = st.selectbox(
        "Decision Mode",
        ["advisor", "rubric", "hybrid"],
        format_func=lambda x: {
            "advisor": "🧠 Advisor (AI-only, no auto-send)",
            "rubric": "📊 Rubric (Rules, auto-send)",
            "hybrid": "🔄 Hybrid (Combined)"
        }[x]
    )
    
    # Start button
    if st.button("🚀 Start Autonomous Browsing", type="primary"):
        # Use existing ProcessCandidate but with CUA
        from yc_matcher.application.autonomous_flow import AutonomousFlow
        flow = AutonomousFlow(...)
        flow.run(your_profile, criteria, template, mode)

def main():
    # Add feature flag check
    if os.getenv("USE_THREE_INPUT_UI") == "true":
        render_three_input_mode()
    else:
        # Keep existing paste mode
        render_paste_mode()  # Current main() content
```

### Test Coverage:
- **Current**: 0 tests ❌
- **Needed**: `tests/unit/test_ui_streamlit.py`

### Environment Variables to Add:
- `USE_THREE_INPUT_UI` - Feature flag for new UI
- `DEFAULT_DECISION_MODE` - Default mode selection
- `AUTO_BROWSE_LIMIT` - Max profiles to process

### Integration Points:
- Line 8: Import ProcessCandidate ✅ Can reuse
- Line 14: Import build_services ✅ Can reuse
- Line 67-74: Evaluation logic ✅ Can reuse

### Effort Estimate:
- **Lines to add**: ~100 new lines
- **Time**: 2 hours
- **Risk**: Low (additive, behind feature flag)
- **Testing**: Add 5-10 UI tests