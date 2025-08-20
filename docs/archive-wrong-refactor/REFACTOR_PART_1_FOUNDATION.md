# Refactor Part 1: Foundation - CUA Integration & Ports

## Overview

This document details Phase 1 of aligning the codebase with documentation. We'll establish the CUA foundation while preserving existing functionality through feature flags.

## Goals

1. Fix CUA browser adapter to be primary driver (not fallback)
2. Define proper ports for autonomous browsing
3. Create decision mode interfaces
4. Add feature flags for safe migration

## Step 1: Fix CUA Browser Adapter

### Current Problem
CUA exists but only handles message sending. It should drive the entire flow.

### File: `src/yc_matcher/infrastructure/openai_cua_browser.py`

```python
# CURRENT (Wrong - only sends messages)
class OpenAICUABrowser:
    async def send_message(self, message: str) -> bool:
        # Only used for sending
        
# REQUIRED (Right - drives entire flow)  
class OpenAICUABrowser:
    async def browse_to_listing(self) -> None:
        """Navigate to YC cofounder listing"""
        
    async def extract_profiles(self) -> List[ProfileData]:
        """Extract all visible profiles from page"""
        
    async def open_profile(self, profile_id: str) -> None:
        """Click into specific profile"""
        
    async def extract_profile_details(self) -> Profile:
        """Extract detailed profile information"""
        
    async def send_message(self, message: str) -> bool:
        """Send message to current profile"""
```

### Implementation Tasks

1. **Extend CUA browser methods** (2 hours)
   - Add browse_to_listing()
   - Add extract_profiles()
   - Add open_profile()
   - Add extract_profile_details()

2. **Fix Responses API usage** (1 hour)
   ```python
   from agents import Agent, ComputerTool, Session
   
   class OpenAICUABrowser:
       def __init__(self):
           self.model = os.getenv("CUA_MODEL")  # From env
           self.agent = Agent(
               model=self.model,
               tools=[ComputerTool()],
               temperature=0.3
           )
           self.session = Session()
   ```

3. **Add screenshot loop** (2 hours)
   ```python
   async def _cua_loop(self, instruction: str) -> Any:
       """Core CUA loop: screenshot → analyze → action → repeat"""
       result = self.agent.run(
           messages=[{"role": "user", "content": instruction}],
           tools=[ComputerTool()],
           session=self.session
       )
       return self._parse_result(result)
   ```

## Step 2: Define Autonomous Browse Port

### File: `src/yc_matcher/application/ports.py`

```python
from typing import Protocol, List, Optional
from ..domain.entities import Profile, Decision

class AutonomousBrowserPort(Protocol):
    """Port for autonomous browser operations via CUA"""
    
    async def start_session(self, base_url: str) -> None:
        """Initialize browser session"""
        
    async def browse_to_listing(self) -> None:
        """Navigate to candidate listing page"""
        
    async def extract_profile_list(self) -> List[dict]:
        """Extract all visible profile summaries"""
        
    async def open_profile(self, profile_id: str) -> None:
        """Navigate to specific profile"""
        
    async def extract_full_profile(self) -> Profile:
        """Extract complete profile details"""
        
    async def send_message(self, message: str) -> bool:
        """Send message to current profile"""
        
    async def close_session(self) -> None:
        """Clean up browser session"""

class DecisionModePort(Protocol):
    """Port for decision mode implementations"""
    
    async def evaluate(
        self,
        profile: Profile,
        your_profile: str,
        criteria: str
    ) -> Decision:
        """Evaluate profile match"""
```

## Step 3: Create Decision Mode Interfaces

### Directory Structure
```
src/yc_matcher/application/decision_modes/
├── __init__.py
├── base.py          # Base interface
├── advisor.py       # LLM-only mode
├── rubric.py        # Deterministic mode
└── hybrid.py        # Combined mode
```

### File: `src/yc_matcher/application/decision_modes/base.py`

```python
from abc import ABC, abstractmethod
from ...domain.entities import Profile, Decision

class DecisionMode(ABC):
    """Base class for all decision modes"""
    
    @abstractmethod
    async def evaluate(
        self,
        profile: Profile,
        your_profile: str,
        criteria: str
    ) -> Decision:
        """Evaluate if profile matches criteria"""
        pass
        
    @property
    @abstractmethod
    def mode_name(self) -> str:
        """Return mode identifier"""
        pass
```

### File: `src/yc_matcher/application/decision_modes/advisor.py`

```python
class AdvisorMode(DecisionMode):
    """Pure LLM evaluation (no auto-send)"""
    
    def __init__(self, llm_adapter):
        self.llm = llm_adapter
        
    async def evaluate(self, profile, your_profile, criteria):
        # Pure LLM reasoning
        prompt = self._build_advisor_prompt(profile, your_profile, criteria)
        response = await self.llm.complete(prompt)
        return self._parse_decision(response)
        
    @property
    def mode_name(self) -> str:
        return "advisor"
```

### File: `src/yc_matcher/application/decision_modes/rubric.py`

```python
class RubricMode(DecisionMode):
    """Deterministic scoring (auto-send if threshold met)"""
    
    def __init__(self, scoring_service, threshold=5.0):
        self.scorer = scoring_service
        self.threshold = threshold
        
    async def evaluate(self, profile, your_profile, criteria):
        # Deterministic scoring
        score = self.scorer.calculate_score(profile, criteria)
        return Decision(
            should_message=score.total >= self.threshold,
            confidence=1.0,
            rationale=f"Score: {score.total:.1f}",
            mode="rubric"
        )
        
    @property
    def mode_name(self) -> str:
        return "rubric"
```

### File: `src/yc_matcher/application/decision_modes/hybrid.py`

```python
class HybridMode(DecisionMode):
    """Weighted combination of advisor + rubric"""
    
    def __init__(self, advisor, rubric, weight=0.5):
        self.advisor = advisor
        self.rubric = rubric
        self.weight = weight  # 0=rubric only, 1=advisor only
        
    async def evaluate(self, profile, your_profile, criteria):
        # Get both evaluations
        advisor_decision = await self.advisor.evaluate(
            profile, your_profile, criteria
        )
        rubric_decision = await self.rubric.evaluate(
            profile, your_profile, criteria
        )
        
        # Weighted combination
        combined_confidence = (
            self.weight * advisor_decision.confidence +
            (1 - self.weight) * rubric_decision.confidence
        )
        
        return Decision(
            should_message=combined_confidence > 0.5,
            confidence=combined_confidence,
            rationale=f"Hybrid: {combined_confidence:.0%}",
            mode="hybrid"
        )
        
    @property  
    def mode_name(self) -> str:
        return "hybrid"
```

## Step 4: Add Feature Flags

### File: `src/yc_matcher/config.py`

```python
import os
from typing import Optional

class FeatureFlags:
    """Centralized feature flag management"""
    
    # Core features
    USE_CUA_PRIMARY = os.getenv("USE_CUA_PRIMARY", "false") == "true"
    USE_THREE_INPUT_UI = os.getenv("USE_THREE_INPUT_UI", "false") == "true"
    USE_DECISION_MODES = os.getenv("USE_DECISION_MODES", "false") == "true"
    
    # Fallback options
    ENABLE_PLAYWRIGHT_FALLBACK = os.getenv("ENABLE_PLAYWRIGHT_FALLBACK", "true") == "true"
    
    # Decision mode configuration
    DEFAULT_DECISION_MODE = os.getenv("DEFAULT_DECISION_MODE", "rubric")
    HYBRID_WEIGHT = float(os.getenv("HYBRID_WEIGHT", "0.5"))
    RUBRIC_THRESHOLD = float(os.getenv("RUBRIC_THRESHOLD", "5.0"))
    
    @classmethod
    def is_enabled(cls, flag: str) -> bool:
        """Check if a feature flag is enabled"""
        return getattr(cls, flag, False)
```

## Step 5: Update Dependency Injection

### File: `src/yc_matcher/interface/di.py`

```python
from ..config import FeatureFlags
from ..application.decision_modes import AdvisorMode, RubricMode, HybridMode

def create_browser() -> BrowserPort:
    """Create browser with feature flag control"""
    if FeatureFlags.USE_CUA_PRIMARY:
        # CUA is primary (new behavior)
        browser = OpenAICUABrowser()
        if FeatureFlags.ENABLE_PLAYWRIGHT_FALLBACK:
            browser = BrowserWithFallback(
                primary=browser,
                fallback=PlaywrightBrowser()
            )
        return browser
    else:
        # Old behavior (backward compatible)
        if os.getenv("ENABLE_CUA") == "1":
            return OpenAICUABrowser()
        elif os.getenv("ENABLE_PLAYWRIGHT") == "1":
            return PlaywrightBrowser()
        return NullBrowser()

def create_decision_mode() -> DecisionMode:
    """Create decision mode based on configuration"""
    if not FeatureFlags.USE_DECISION_MODES:
        # Old behavior - use existing adapters
        return LegacyDecisionAdapter()
        
    mode = FeatureFlags.DEFAULT_DECISION_MODE
    
    if mode == "advisor":
        return AdvisorMode(create_llm_adapter())
    elif mode == "rubric":
        return RubricMode(
            create_scoring_service(),
            FeatureFlags.RUBRIC_THRESHOLD
        )
    elif mode == "hybrid":
        return HybridMode(
            AdvisorMode(create_llm_adapter()),
            RubricMode(create_scoring_service()),
            FeatureFlags.HYBRID_WEIGHT
        )
    else:
        raise ValueError(f"Unknown decision mode: {mode}")
```

## Step 6: Create Tests for New Components

### File: `tests/unit/test_openai_cua_browser.py`

```python
import pytest
from unittest.mock import Mock, patch
from yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser

class TestOpenAICUABrowser:
    @patch('yc_matcher.infrastructure.openai_cua_browser.Agent')
    def test_initialization(self, mock_agent):
        """Test CUA browser initializes with env config"""
        with patch.dict('os.environ', {'CUA_MODEL': 'test-model'}):
            browser = OpenAICUABrowser()
            assert browser.model == 'test-model'
            mock_agent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_browse_to_listing(self):
        """Test navigation to YC listing"""
        browser = OpenAICUABrowser()
        browser.agent = Mock()
        
        await browser.browse_to_listing()
        
        browser.agent.run.assert_called_with(
            messages=ANY,
            tools=[ComputerTool()],
            session=ANY
        )
    
    @pytest.mark.asyncio
    async def test_extract_profiles(self):
        """Test profile extraction from page"""
        # Test implementation
        
    @pytest.mark.asyncio
    async def test_fallback_on_error(self):
        """Test fallback to Playwright on CUA error"""
        # Test implementation
```

### File: `tests/unit/test_decision_modes.py`

```python
import pytest
from yc_matcher.application.decision_modes import (
    AdvisorMode, RubricMode, HybridMode
)

class TestAdvisorMode:
    @pytest.mark.asyncio
    async def test_llm_only_evaluation(self):
        """Test advisor mode uses only LLM"""
        llm = Mock()
        llm.complete.return_value = "YES: Good match"
        
        mode = AdvisorMode(llm)
        decision = await mode.evaluate(profile, your_profile, criteria)
        
        assert decision.mode == "advisor"
        assert llm.complete.called

class TestRubricMode:
    def test_deterministic_scoring(self):
        """Test rubric mode is deterministic"""
        scorer = Mock()
        scorer.calculate_score.return_value = Score(total=6.0)
        
        mode = RubricMode(scorer, threshold=5.0)
        decision = await mode.evaluate(profile, your_profile, criteria)
        
        assert decision.should_message is True
        assert decision.confidence == 1.0
        assert decision.mode == "rubric"

class TestHybridMode:
    @pytest.mark.asyncio
    async def test_weighted_combination(self):
        """Test hybrid combines advisor and rubric"""
        advisor = Mock()
        advisor.evaluate.return_value = Decision(confidence=0.8)
        
        rubric = Mock()  
        rubric.evaluate.return_value = Decision(confidence=0.6)
        
        mode = HybridMode(advisor, rubric, weight=0.7)
        decision = await mode.evaluate(profile, your_profile, criteria)
        
        # 0.7 * 0.8 + 0.3 * 0.6 = 0.74
        assert decision.confidence == pytest.approx(0.74)
```

## Migration Checklist

### Week 1 Tasks
- [ ] Implement extended CUA browser methods
- [ ] Create decision mode classes
- [ ] Add feature flags to config
- [ ] Update dependency injection
- [ ] Write unit tests for new components

### Testing Strategy
1. All new code behind feature flags (safe)
2. Existing tests continue passing
3. New tests for new components
4. Integration tests for both paths

### Rollout Plan
1. Deploy with all flags disabled (no change)
2. Enable for internal testing
3. Gradual rollout by percentage
4. Monitor metrics and errors
5. Full migration when stable

## Success Criteria

- [ ] CUA browser implements full autonomous flow
- [ ] Three decision modes available
- [ ] Feature flags control behavior
- [ ] All existing tests pass
- [ ] New component tests pass
- [ ] Zero impact when flags disabled

## Next Phase

Once foundation is complete, proceed to [REFACTOR_PART_2_CORE_FLOW.md](./REFACTOR_PART_2_CORE_FLOW.md) to update use cases and integrate CUA into the main flow.