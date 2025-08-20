# Refactor Part 3: Interface - UI Transformation to 3-Input

## Overview

This document details Phase 3 of the refactoring: transforming the Streamlit UI from paste-based to the documented 3-input autonomous flow.

## Goals

1. Create new 3-input UI panel
2. Add decision mode selector
3. Implement real-time progress display
4. Maintain backward compatibility via feature flags

## Step 1: Create New 3-Input UI

### File: `src/yc_matcher/interface/web/ui_streamlit_v2.py`

```python
import streamlit as st
from typing import Dict, Any
from ...config import FeatureFlags

def render_three_input_ui():
    """Render the new 3-input autonomous UI"""
    
    st.title("🚀 YC Co-Founder Matcher - Autonomous Mode")
    
    # Three main input columns
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.subheader("📝 Your Profile")
        your_profile = st.text_area(
            "Describe yourself",
            placeholder="""Example:
Technical co-founder
- 5 years Python/FastAPI
- Built ML pipeline at Scale
- Looking for B2B SaaS
- Based in NYC""",
            height=200,
            key="your_profile"
        )
        
    with col2:
        st.subheader("🎯 Match Criteria")
        match_criteria = st.text_area(
            "What you're looking for",
            placeholder="""Example:
- Business/sales background
- B2B experience preferred
- NYC or remote
- Passionate about AI/ML
- Avoid: crypto, gaming""",
            height=200,
            key="match_criteria"
        )
        
    with col3:
        st.subheader("💬 Message Template")
        message_template = st.text_area(
            "Your outreach message",
            placeholder="""Hi [Name],

I saw your profile and was impressed by [specific_skill]. I'm building [your_project] and your experience with [their_background] would be invaluable.

Would love to chat about potential collaboration.

Best,
[Your name]""",
            height=200,
            key="message_template"
        )
    
    # Decision mode configuration
    st.markdown("---")
    
    mode_col, config_col = st.columns([1, 2])
    
    with mode_col:
        st.subheader("⚙️ Decision Mode")
        decision_mode = st.selectbox(
            "How should matches be evaluated?",
            options=["advisor", "rubric", "hybrid"],
            format_func=lambda x: {
                "advisor": "🧠 Advisor (AI-only, no auto-send)",
                "rubric": "📊 Rubric (Rule-based, auto-send)",
                "hybrid": "🔄 Hybrid (Combined, selective send)"
            }[x],
            key="decision_mode"
        )
        
    with config_col:
        st.subheader("🎛️ Mode Configuration")
        
        if decision_mode == "advisor":
            st.info("💡 AI will evaluate matches but won't auto-send messages")
            temperature = st.slider(
                "AI Creativity",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1,
                key="advisor_temperature"
            )
            
        elif decision_mode == "rubric":
            st.warning("⚡ Messages auto-sent when score threshold met")
            threshold = st.slider(
                "Score Threshold",
                min_value=0,
                max_value=10,
                value=5,
                step=1,
                key="rubric_threshold"
            )
            st.caption(f"Auto-send if score ≥ {threshold}")
            
        elif decision_mode == "hybrid":
            st.success("🔄 Combines AI and rules for best results")
            col_a, col_b = st.columns(2)
            with col_a:
                ai_weight = st.slider(
                    "AI Weight",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.1,
                    key="hybrid_weight"
                )
            with col_b:
                confidence_threshold = st.slider(
                    "Send Confidence",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    step=0.1,
                    key="confidence_threshold"
                )
            st.caption(f"AI: {ai_weight:.0%} | Rules: {1-ai_weight:.0%}")
    
    # Processing controls
    st.markdown("---")
    
    control_col1, control_col2, control_col3 = st.columns([1, 1, 1])
    
    with control_col1:
        st.subheader("🎯 Limits")
        profile_limit = st.number_input(
            "Max profiles to evaluate",
            min_value=1,
            max_value=100,
            value=20,
            step=5,
            key="profile_limit"
        )
        
        message_limit = st.number_input(
            "Max messages to send",
            min_value=0,
            max_value=50,
            value=10,
            step=5,
            key="message_limit"
        )
        
    with control_col2:
        st.subheader("⏱️ Pacing")
        send_delay = st.slider(
            "Delay between messages (seconds)",
            min_value=0,
            max_value=60,
            value=5,
            step=5,
            key="send_delay"
        )
        
        st.checkbox(
            "🔄 Continue from last position",
            value=False,
            key="continue_from_last"
        )
        
    with control_col3:
        st.subheader("🛡️ Safety")
        
        st.checkbox(
            "✅ Enable STOP file monitoring",
            value=True,
            key="enable_stop_flag"
        )
        
        st.checkbox(
            "📊 Respect daily/weekly quotas",
            value=True,
            key="respect_quotas"
        )
        
        dry_run = st.checkbox(
            "🧪 Dry run (no actual sends)",
            value=False,
            key="dry_run"
        )
    
    # Validation
    inputs_valid = all([
        your_profile.strip(),
        match_criteria.strip(),
        message_template.strip()
    ])
    
    # Start button
    st.markdown("---")
    
    if st.button(
        "🚀 Start Autonomous Matching",
        disabled=not inputs_valid,
        type="primary",
        use_container_width=True
    ):
        if not inputs_valid:
            st.error("Please fill in all three input fields")
        else:
            return {
                'action': 'start',
                'your_profile': your_profile,
                'match_criteria': match_criteria,
                'message_template': message_template,
                'decision_mode': decision_mode,
                'config': {
                    'profile_limit': profile_limit,
                    'message_limit': message_limit,
                    'send_delay': send_delay,
                    'dry_run': dry_run,
                    'continue_from_last': st.session_state.get('continue_from_last', False)
                },
                'mode_config': _get_mode_config(decision_mode)
            }
    
    # Help section
    with st.expander("❓ Need Help?"):
        st.markdown("""
        ### How it works:
        1. **Your Profile**: Describe your background and what you bring
        2. **Match Criteria**: Define your ideal co-founder
        3. **Message Template**: Craft your outreach (use [Name] placeholder)
        
        ### Decision Modes:
        - **Advisor**: AI evaluates but you manually send messages
        - **Rubric**: Automatic rule-based sending when threshold met
        - **Hybrid**: Combines AI and rules for balanced automation
        
        ### Safety Features:
        - Create a `STOP` file to immediately halt processing
        - Daily/weekly quotas prevent over-messaging
        - Dry run mode for testing without sending
        """)
        
    return None

def _get_mode_config(mode: str) -> Dict[str, Any]:
    """Extract mode-specific configuration"""
    if mode == "advisor":
        return {
            'temperature': st.session_state.get('advisor_temperature', 0.3)
        }
    elif mode == "rubric":
        return {
            'threshold': st.session_state.get('rubric_threshold', 5)
        }
    elif mode == "hybrid":
        return {
            'ai_weight': st.session_state.get('hybrid_weight', 0.5),
            'confidence_threshold': st.session_state.get('confidence_threshold', 0.7)
        }
    return {}
```

## Step 2: Create Progress Display Component

### File: `src/yc_matcher/interface/web/components/progress_display.py`

```python
import streamlit as st
from typing import List, Dict, Any
import time

class ProgressDisplay:
    """Real-time progress display for autonomous processing"""
    
    def __init__(self):
        self.container = st.container()
        self.progress_bar = None
        self.status_text = None
        self.results_table = None
        
    def initialize(self, total_profiles: int):
        """Initialize progress display components"""
        with self.container:
            st.subheader("🔄 Processing Progress")
            
            # Progress bar
            self.progress_bar = st.progress(0)
            
            # Status text
            self.status_text = st.empty()
            self.status_text.text("Initializing browser...")
            
            # Metrics row
            self.metrics = st.columns(4)
            self.metric_evaluated = self.metrics[0].metric("Evaluated", 0)
            self.metric_matched = self.metrics[1].metric("Matched", 0)
            self.metric_sent = self.metrics[2].metric("Sent", 0)
            self.metric_skipped = self.metrics[3].metric("Skipped", 0)
            
            # Results table placeholder
            st.subheader("📊 Results")
            self.results_placeholder = st.empty()
            
    def update(
        self,
        current: int,
        total: int,
        status: str,
        results: List[Dict[str, Any]]
    ):
        """Update progress display"""
        
        # Update progress bar
        progress = current / total if total > 0 else 0
        self.progress_bar.progress(progress)
        
        # Update status
        self.status_text.text(f"{status} ({current}/{total})")
        
        # Update metrics
        evaluated = len(results)
        matched = sum(1 for r in results if r['decision'].should_message)
        sent = sum(1 for r in results if r.get('sent', False))
        skipped = sum(1 for r in results if r.get('skipped', False))
        
        self.metrics[0].metric("Evaluated", evaluated)
        self.metrics[1].metric("Matched", matched)
        self.metrics[2].metric("Sent", sent)
        self.metrics[3].metric("Skipped", skipped)
        
        # Update results table
        if results:
            self._update_results_table(results)
            
    def _update_results_table(self, results: List[Dict[str, Any]]):
        """Update the results table display"""
        
        # Convert to display format
        display_data = []
        for r in results[-10:]:  # Show last 10
            profile = r['profile']
            decision = r['decision']
            
            display_data.append({
                'Name': profile.name[:20],
                'Score': f"{decision.confidence:.1%}",
                'Decision': '✅' if decision.should_message else '❌',
                'Mode': decision.mode,
                'Sent': '📤' if r.get('sent') else '⏳',
                'Reason': decision.rationale[:30]
            })
            
        # Display as dataframe
        import pandas as pd
        df = pd.DataFrame(display_data)
        self.results_placeholder.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
    def show_complete(self, summary: Dict[str, Any]):
        """Show completion summary"""
        with self.container:
            st.success("✅ Processing Complete!")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total Evaluated",
                    summary['total_evaluated'],
                    delta=None
                )
                
            with col2:
                st.metric(
                    "Messages Sent",
                    summary['total_sent'],
                    delta=f"{summary['send_rate']:.0%} send rate"
                )
                
            with col3:
                st.metric(
                    "Time Taken",
                    f"{summary['duration']:.1f}s",
                    delta=f"{summary['per_profile']:.1f}s per profile"
                )
```

## Step 3: Update Main Streamlit App

### File: `src/yc_matcher/interface/web/ui_streamlit.py`

```python
import streamlit as st
from ...config import FeatureFlags
from .ui_streamlit_v2 import render_three_input_ui
from .ui_streamlit_legacy import render_legacy_ui
from .components.progress_display import ProgressDisplay

def main():
    """Main Streamlit application"""
    
    st.set_page_config(
        page_title="YC Co-Founder Matcher",
        page_icon="🚀",
        layout="wide"
    )
    
    # Feature flag check
    if FeatureFlags.USE_THREE_INPUT_UI:
        # New 3-input UI
        render_new_ui()
    else:
        # Legacy paste-based UI
        render_legacy_with_preview()
        
def render_new_ui():
    """Render the new 3-input autonomous UI"""
    
    # Get inputs
    inputs = render_three_input_ui()
    
    if inputs and inputs['action'] == 'start':
        # Process with progress display
        process_with_progress(inputs)
        
def render_legacy_with_preview():
    """Render legacy UI with optional preview of new UI"""
    
    # Sidebar option to preview new UI
    with st.sidebar:
        st.subheader("🆕 Preview New UI")
        preview_new = st.checkbox(
            "Show new 3-input interface",
            value=False,
            help="Preview the upcoming autonomous interface"
        )
        
    if preview_new:
        st.info("👀 **Preview Mode** - This is the new interface coming soon!")
        render_three_input_ui()
    else:
        render_legacy_ui()
        
def process_with_progress(inputs: Dict[str, Any]):
    """Process matches with real-time progress display"""
    
    # Initialize progress display
    progress = ProgressDisplay()
    progress.initialize(inputs['config']['profile_limit'])
    
    # Create processor
    from ...interface.di import Dependencies
    deps = Dependencies()
    processor = deps.create_autonomous_processor()
    
    # Process with streaming updates
    import asyncio
    
    async def run_processing():
        results = []
        async for update in processor.process_streaming(
            your_profile=inputs['your_profile'],
            match_criteria=inputs['match_criteria'],
            message_template=inputs['message_template'],
            limit=inputs['config']['profile_limit'],
            mode=inputs['decision_mode'],
            mode_config=inputs['mode_config']
        ):
            results.append(update)
            
            # Update progress display
            progress.update(
                current=len(results),
                total=inputs['config']['profile_limit'],
                status=f"Processing {update['profile'].name}",
                results=results
            )
            
            # Check for stop
            if st.session_state.get('stop_requested', False):
                break
                
        # Show completion
        summary = {
            'total_evaluated': len(results),
            'total_sent': sum(1 for r in results if r.get('sent')),
            'send_rate': sum(1 for r in results if r.get('sent')) / len(results),
            'duration': sum(r.get('duration', 0) for r in results),
            'per_profile': sum(r.get('duration', 0) for r in results) / len(results)
        }
        progress.show_complete(summary)
        
    # Run async processing
    asyncio.run(run_processing())
```

## Step 4: Create Legacy UI Module

### File: `src/yc_matcher/interface/web/ui_streamlit_legacy.py`

```python
import streamlit as st

def render_legacy_ui():
    """Render the legacy paste-based UI for backward compatibility"""
    
    st.title("YC Co-Founder Matcher - Classic Mode")
    
    st.warning("""
    ⚠️ **Legacy Interface** - This paste-based interface will be deprecated.
    Try the new 3-input autonomous mode in the sidebar!
    """)
    
    # Main input area
    profile_text = st.text_area(
        "Paste candidate profile text here",
        height=300,
        placeholder="Copy and paste the full profile text from YC..."
    )
    
    # Sidebar for criteria and template
    with st.sidebar:
        st.subheader("Evaluation Criteria")
        criteria = st.text_area(
            "What are you looking for?",
            height=150
        )
        
        st.subheader("Message Template")
        template = st.text_area(
            "Your message template",
            height=150
        )
        
        st.subheader("Settings")
        auto_send = st.checkbox("Auto-send messages", value=False)
        
    # Evaluate button
    if st.button("Evaluate Profile", type="primary"):
        if not profile_text:
            st.error("Please paste a profile to evaluate")
        else:
            # Process with legacy processor
            from ...interface.di import Dependencies
            deps = Dependencies()
            processor = deps.create_legacy_processor()
            
            result = processor(
                profile_text=profile_text,
                criteria=criteria,
                template=template
            )
            
            # Display results
            display_legacy_results(result)
            
def display_legacy_results(result):
    """Display results in legacy format"""
    
    decision = result['decision']
    
    if decision.should_message:
        st.success(f"✅ **YES** - {decision.rationale}")
        
        if result.get('message'):
            st.subheader("Drafted Message:")
            st.text_area("Message", value=result['message'], height=200)
            
            if st.button("Send Message"):
                # Send via browser
                st.info("Sending message...")
    else:
        st.error(f"❌ **NO** - {decision.rationale}")
```

## Step 5: Add UI Tests

### File: `tests/unit/test_ui_components.py`

```python
import pytest
from unittest.mock import Mock, patch
import streamlit as st
from yc_matcher.interface.web.ui_streamlit_v2 import render_three_input_ui

class TestThreeInputUI:
    @patch('streamlit.text_area')
    @patch('streamlit.selectbox')
    @patch('streamlit.button')
    def test_renders_three_inputs(self, mock_button, mock_select, mock_text):
        """Test that UI renders three input fields"""
        
        mock_text.side_effect = [
            "Your profile text",
            "Match criteria text",
            "Message template text"
        ]
        mock_select.return_value = "rubric"
        mock_button.return_value = True
        
        result = render_three_input_ui()
        
        assert mock_text.call_count == 3
        assert result is not None
        assert result['your_profile'] == "Your profile text"
        assert result['match_criteria'] == "Match criteria text"
        assert result['message_template'] == "Message template text"
        
    def test_decision_mode_configuration(self):
        """Test decision mode configuration options"""
        # Test implementation
        
    def test_validation_requires_all_fields(self):
        """Test that all three fields are required"""
        # Test implementation
```

### File: `tests/integration/test_ui_flow.py`

```python
import pytest
from streamlit.testing.v1 import AppTest

class TestUIFlow:
    def test_three_input_flow(self):
        """Test complete UI flow with 3 inputs"""
        
        at = AppTest.from_file("src/yc_matcher/interface/web/ui_streamlit.py")
        at.run()
        
        # Fill in three inputs
        at.text_area[0].set_value("My profile")
        at.text_area[1].set_value("My criteria")  
        at.text_area[2].set_value("My template")
        
        # Select decision mode
        at.selectbox[0].set_value("hybrid")
        
        # Click start
        at.button[0].click()
        
        # Verify processing started
        assert "Processing Progress" in at.markdown[0].value
```

## Step 6: Migration Strategy

### Gradual UI Rollout

```python
# config.py additions
class UIConfig:
    # Rollout percentage
    UI_ROLLOUT_PERCENTAGE = float(os.getenv("UI_ROLLOUT_PCT", "0"))
    
    # User allowlist for early access
    UI_ALLOWLIST = os.getenv("UI_ALLOWLIST", "").split(",")
    
    @classmethod
    def should_show_new_ui(cls, user_id: str = None) -> bool:
        """Determine if user should see new UI"""
        
        # Check allowlist
        if user_id and user_id in cls.UI_ALLOWLIST:
            return True
            
        # Check rollout percentage
        import random
        return random.random() < cls.UI_ROLLOUT_PERCENTAGE
```

## Deployment Checklist

### Phase 1: Internal Testing
- [ ] Deploy with `USE_THREE_INPUT_UI=false`
- [ ] Enable for team via allowlist
- [ ] Test all three decision modes
- [ ] Verify progress display

### Phase 2: Beta Release (10%)
- [ ] Set `UI_ROLLOUT_PCT=0.1`
- [ ] Monitor user feedback
- [ ] Track completion rates
- [ ] Fix reported issues

### Phase 3: Wider Release (50%)
- [ ] Set `UI_ROLLOUT_PCT=0.5`
- [ ] A/B test metrics
- [ ] Compare conversion rates
- [ ] Optimize based on data

### Phase 4: Full Release
- [ ] Set `USE_THREE_INPUT_UI=true`
- [ ] Remove legacy UI code
- [ ] Update documentation
- [ ] Announce to users

## Success Criteria

- [ ] Three input fields capture user data
- [ ] Decision modes configurable in UI
- [ ] Real-time progress display works
- [ ] Legacy UI still accessible via flag
- [ ] All UI tests pass
- [ ] No performance degradation

## Next Phase

Once UI is complete, proceed to [REFACTOR_PART_4_VALIDATION.md](./REFACTOR_PART_4_VALIDATION.md) for comprehensive testing and deployment validation.