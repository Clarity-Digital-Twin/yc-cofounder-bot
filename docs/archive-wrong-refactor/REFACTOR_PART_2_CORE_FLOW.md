# Refactor Part 2: Core Flow - Use Cases & Decision Pipeline

## Overview

This document details Phase 2 of the refactoring: transforming the core application flow from paste-based to autonomous CUA-driven browsing with proper decision modes.

## Goals

1. Create new autonomous use case
2. Integrate CUA browser into main flow
3. Wire up decision modes
4. Maintain backward compatibility

## Step 1: Create Autonomous Process Use Case

### File: `src/yc_matcher/application/use_cases/process_autonomous.py`

```python
from typing import List, Optional
from ..ports import AutonomousBrowserPort, DecisionModePort
from ...domain.entities import Profile, Decision, ProcessingResult

class ProcessAutonomous:
    """Use case for autonomous CUA-driven matching"""
    
    def __init__(
        self,
        browser: AutonomousBrowserPort,
        decision_mode: DecisionModePort,
        quota_service,
        progress_tracker,
        stop_flag,
        logger
    ):
        self.browser = browser
        self.decision_mode = decision_mode
        self.quota = quota_service
        self.progress = progress_tracker
        self.stop_flag = stop_flag
        self.logger = logger
        
    async def __call__(
        self,
        your_profile: str,
        match_criteria: str,
        message_template: str,
        limit: int = 20
    ) -> ProcessingResult:
        """
        Main autonomous processing flow:
        1. CUA browses to YC listing
        2. Extracts visible profiles
        3. Evaluates each with decision mode
        4. Sends messages when appropriate
        """
        
        # Initialize browser session
        await self.browser.start_session(self._get_yc_url())
        
        try:
            # Navigate to listing
            await self.browser.browse_to_listing()
            
            # Extract profile list
            profile_summaries = await self.browser.extract_profile_list()
            
            results = []
            sent_count = 0
            
            for summary in profile_summaries[:limit]:
                # Check stop flag
                if self.stop_flag.should_stop():
                    self.logger.log("STOP flag detected")
                    break
                    
                # Check quotas
                if not self.quota.can_send():
                    self.logger.log("Quota exceeded")
                    break
                    
                # Open individual profile
                await self.browser.open_profile(summary['id'])
                
                # Extract full profile
                profile = await self.browser.extract_full_profile()
                
                # Make decision
                decision = await self.decision_mode.evaluate(
                    profile=profile,
                    your_profile=your_profile,
                    criteria=match_criteria
                )
                
                # Log decision
                self.logger.log_decision(profile, decision)
                
                # Send message if YES
                if decision.should_message and self._should_auto_send(decision):
                    message = self._render_message(
                        template=message_template,
                        profile=profile,
                        decision=decision
                    )
                    
                    success = await self.browser.send_message(message)
                    
                    if success:
                        sent_count += 1
                        self.quota.record_send()
                        self.progress.mark_sent(profile.id)
                        
                results.append({
                    'profile': profile,
                    'decision': decision,
                    'sent': decision.should_message
                })
                
            return ProcessingResult(
                total_evaluated=len(results),
                total_sent=sent_count,
                results=results
            )
            
        finally:
            await self.browser.close_session()
            
    def _should_auto_send(self, decision: Decision) -> bool:
        """Determine if message should be auto-sent based on mode"""
        if decision.mode == "advisor":
            return False  # Advisor never auto-sends
        elif decision.mode == "rubric":
            return True   # Rubric always auto-sends if YES
        elif decision.mode == "hybrid":
            return decision.confidence > 0.7  # Hybrid needs high confidence
        return False
        
    def _render_message(self, template: str, profile: Profile, decision: Decision) -> str:
        """Render message from template"""
        # Implementation here
        pass
```

## Step 2: Update Existing Use Case for Compatibility

### File: `src/yc_matcher/application/use_cases/process_candidate.py`

```python
from ...config import FeatureFlags

class ProcessCandidate:
    """Legacy use case - maintained for backward compatibility"""
    
    def __call__(self, profile_text: str, criteria: str, template: str):
        if FeatureFlags.USE_CUA_PRIMARY:
            # Redirect to autonomous flow
            return self._process_autonomous(profile_text, criteria, template)
        else:
            # Original paste-based flow
            return self._process_legacy(profile_text, criteria, template)
            
    def _process_autonomous(self, profile_text, criteria, template):
        """Bridge to autonomous flow for compatibility"""
        # Parse profile_text as if it were "your profile"
        # Use it with autonomous processor
        processor = ProcessAutonomous(...)
        return processor(
            your_profile=profile_text,  # Repurpose input
            match_criteria=criteria,
            message_template=template
        )
        
    def _process_legacy(self, profile_text, criteria, template):
        """Original implementation"""
        # Keep existing code here
```

## Step 3: Create Decision Mode Factory

### File: `src/yc_matcher/application/factories/decision_factory.py`

```python
from typing import Optional
from ...config import FeatureFlags
from ..decision_modes import AdvisorMode, RubricMode, HybridMode

class DecisionModeFactory:
    """Factory for creating decision mode instances"""
    
    @staticmethod
    def create(
        mode: Optional[str] = None,
        llm_adapter = None,
        scoring_service = None
    ) -> DecisionModePort:
        """
        Create decision mode based on configuration
        
        Args:
            mode: Override mode (if None, uses config)
            llm_adapter: LLM service for advisor mode
            scoring_service: Scoring for rubric mode
        """
        
        # Determine mode
        if mode is None:
            mode = FeatureFlags.DEFAULT_DECISION_MODE
            
        # Validate mode
        valid_modes = ["advisor", "rubric", "hybrid"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {valid_modes}")
            
        # Create appropriate mode
        if mode == "advisor":
            if not llm_adapter:
                raise ValueError("Advisor mode requires llm_adapter")
            return AdvisorMode(llm_adapter)
            
        elif mode == "rubric":
            if not scoring_service:
                raise ValueError("Rubric mode requires scoring_service")
            return RubricMode(
                scoring_service,
                threshold=FeatureFlags.RUBRIC_THRESHOLD
            )
            
        elif mode == "hybrid":
            if not llm_adapter or not scoring_service:
                raise ValueError("Hybrid mode requires both llm_adapter and scoring_service")
            
            advisor = AdvisorMode(llm_adapter)
            rubric = RubricMode(scoring_service, FeatureFlags.RUBRIC_THRESHOLD)
            
            return HybridMode(
                advisor=advisor,
                rubric=rubric,
                weight=FeatureFlags.HYBRID_WEIGHT
            )
```

## Step 4: Update Main Application Entry Point

### File: `src/yc_matcher/interface/web/app.py`

```python
from ...config import FeatureFlags
from ...application.use_cases import ProcessCandidate, ProcessAutonomous

class YCMatcherApp:
    """Main application controller"""
    
    def __init__(self, dependencies):
        self.deps = dependencies
        
        # Choose processor based on feature flags
        if FeatureFlags.USE_CUA_PRIMARY:
            self.processor = self._create_autonomous_processor()
        else:
            self.processor = self._create_legacy_processor()
            
    def _create_autonomous_processor(self):
        """Create autonomous CUA-driven processor"""
        return ProcessAutonomous(
            browser=self.deps.create_browser(),
            decision_mode=self.deps.create_decision_mode(),
            quota_service=self.deps.create_quota_service(),
            progress_tracker=self.deps.create_progress_tracker(),
            stop_flag=self.deps.create_stop_flag(),
            logger=self.deps.create_logger()
        )
        
    def _create_legacy_processor(self):
        """Create legacy paste-based processor"""
        return ProcessCandidate(
            decision_adapter=self.deps.create_decision_adapter(),
            browser=self.deps.create_browser(),
            quota_service=self.deps.create_quota_service(),
            logger=self.deps.create_logger()
        )
        
    async def process_matches(self, inputs):
        """Process matches with appropriate processor"""
        if FeatureFlags.USE_THREE_INPUT_UI:
            # New 3-input flow
            return await self.processor(
                your_profile=inputs['your_profile'],
                match_criteria=inputs['criteria'],
                message_template=inputs['template'],
                limit=inputs.get('limit', 20)
            )
        else:
            # Legacy paste flow
            return self.processor(
                profile_text=inputs['profile_text'],
                criteria=inputs['criteria'],
                template=inputs['template']
            )
```

## Step 5: Create Integration Tests

### File: `tests/integration/test_autonomous_flow.py`

```python
import pytest
from unittest.mock import Mock, AsyncMock
from yc_matcher.application.use_cases import ProcessAutonomous

class TestAutonomousFlow:
    @pytest.mark.asyncio
    async def test_complete_autonomous_flow(self):
        """Test full autonomous browsing and matching flow"""
        
        # Setup mocks
        browser = AsyncMock()
        browser.extract_profile_list.return_value = [
            {'id': '1', 'name': 'Alice'},
            {'id': '2', 'name': 'Bob'}
        ]
        browser.extract_full_profile.side_effect = [
            Profile(id='1', name='Alice', skills=['Python', 'ML']),
            Profile(id='2', name='Bob', skills=['JavaScript'])
        ]
        
        decision_mode = AsyncMock()
        decision_mode.evaluate.side_effect = [
            Decision(should_message=True, confidence=0.9, mode='rubric'),
            Decision(should_message=False, confidence=0.3, mode='rubric')
        ]
        
        processor = ProcessAutonomous(
            browser=browser,
            decision_mode=decision_mode,
            quota_service=Mock(can_send=lambda: True),
            progress_tracker=Mock(),
            stop_flag=Mock(should_stop=lambda: False),
            logger=Mock()
        )
        
        # Execute
        result = await processor(
            your_profile="Python developer",
            match_criteria="Python, ML",
            message_template="Hi [Name]",
            limit=2
        )
        
        # Verify
        assert result.total_evaluated == 2
        assert result.total_sent == 1  # Only Alice
        assert browser.send_message.call_count == 1
        
    @pytest.mark.asyncio
    async def test_stop_flag_halts_processing(self):
        """Test that STOP flag immediately stops processing"""
        
        browser = AsyncMock()
        browser.extract_profile_list.return_value = [
            {'id': str(i)} for i in range(10)
        ]
        
        stop_flag = Mock()
        stop_flag.should_stop.side_effect = [False, False, True]  # Stop after 2
        
        processor = ProcessAutonomous(
            browser=browser,
            decision_mode=AsyncMock(),
            quota_service=Mock(can_send=lambda: True),
            progress_tracker=Mock(),
            stop_flag=stop_flag,
            logger=Mock()
        )
        
        result = await processor(
            your_profile="Test",
            match_criteria="Test",
            message_template="Test",
            limit=10
        )
        
        assert result.total_evaluated == 2  # Stopped early
```

### File: `tests/integration/test_decision_pipeline.py`

```python
import pytest
from yc_matcher.application.factories import DecisionModeFactory

class TestDecisionPipeline:
    def test_factory_creates_correct_modes(self):
        """Test factory creates appropriate decision modes"""
        
        llm = Mock()
        scorer = Mock()
        
        # Test each mode
        advisor = DecisionModeFactory.create("advisor", llm, scorer)
        assert advisor.mode_name == "advisor"
        
        rubric = DecisionModeFactory.create("rubric", llm, scorer)
        assert rubric.mode_name == "rubric"
        
        hybrid = DecisionModeFactory.create("hybrid", llm, scorer)
        assert hybrid.mode_name == "hybrid"
        
    @pytest.mark.asyncio
    async def test_mode_switching(self):
        """Test switching between decision modes"""
        
        # Setup
        profile = Profile(name="Test", skills=["Python"])
        your_profile = "Python dev"
        criteria = "Python"
        
        llm = AsyncMock()
        llm.complete.return_value = "YES: Good match"
        
        scorer = Mock()
        scorer.calculate_score.return_value = Score(total=6.0)
        
        # Test each mode produces different results
        advisor = DecisionModeFactory.create("advisor", llm, scorer)
        advisor_decision = await advisor.evaluate(profile, your_profile, criteria)
        
        rubric = DecisionModeFactory.create("rubric", llm, scorer)
        rubric_decision = await rubric.evaluate(profile, your_profile, criteria)
        
        # Verify different behaviors
        assert advisor_decision.mode == "advisor"
        assert rubric_decision.mode == "rubric"
        assert rubric_decision.confidence == 1.0  # Deterministic
```

## Step 6: Migration Path

### Environment Variables for Gradual Rollout

```bash
# Phase 1: Everything disabled (current behavior)
USE_CUA_PRIMARY=false
USE_THREE_INPUT_UI=false
USE_DECISION_MODES=false

# Phase 2: Enable CUA but keep old UI
USE_CUA_PRIMARY=true
USE_THREE_INPUT_UI=false
USE_DECISION_MODES=true
DEFAULT_DECISION_MODE=rubric

# Phase 3: Enable new UI with CUA
USE_CUA_PRIMARY=true
USE_THREE_INPUT_UI=true
USE_DECISION_MODES=true
DEFAULT_DECISION_MODE=hybrid

# Phase 4: Full migration
# Remove feature flags, make new behavior default
```

## Testing Strategy

### Unit Tests
- Test each decision mode in isolation
- Test factory creation logic
- Test use case with mocked dependencies

### Integration Tests
- Test complete autonomous flow
- Test decision pipeline
- Test mode switching
- Test safety features (stop, quota)

### E2E Tests
- Test with real CUA browser (requires API key)
- Test fallback scenarios
- Test error recovery

## Rollback Plan

If issues arise:

1. **Immediate**: Set `USE_CUA_PRIMARY=false`
2. **Quick Fix**: Deploy hotfix, re-enable gradually
3. **Full Rollback**: Revert to previous version

## Success Criteria

- [ ] Autonomous use case processes profiles via CUA
- [ ] Decision modes evaluate correctly
- [ ] Factory creates appropriate modes
- [ ] Legacy flow still works when flags disabled
- [ ] Integration tests pass
- [ ] No performance degradation

## Next Phase

Once core flow is complete, proceed to [REFACTOR_PART_3_INTERFACE.md](./REFACTOR_PART_3_INTERFACE.md) to transform the UI to 3-input panel.