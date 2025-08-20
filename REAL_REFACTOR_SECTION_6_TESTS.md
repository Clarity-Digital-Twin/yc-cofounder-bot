# Section 6: Test Coverage

## Current Test Files (18 files):

### Integration Tests (3 files):
- `test_browser_port.py` - Tests Playwright browser
- `test_marker_smoke.py` - Basic smoke test
- `test_sqlite_repo.py` - SQLite repository tests

### Unit Tests (15 files):
- `test_gated_decision.py` ✅ - Threshold gating
- `test_logger_jsonl.py` ✅ - JSONL logging
- `test_logger_stamps.py` ✅ - Stamped logging
- `test_normalizer.py` ✅ - Text normalization
- `test_openai_decision_adapter.py` ✅ - OpenAI decisions (mocked)
- `test_process_candidate.py` ✅ - Main flow
- `test_process_candidate_stop.py` ✅ - Stop flag
- `test_schema.py` ✅ - Pydantic schemas
- `test_scoring.py` ✅ - Weighted scoring
- `test_send_verify.py` ✅ - Message sending
- `test_sqlite_progress.py` ✅ - Progress tracking
- `test_sqlite_quota.py` ✅ - Quota management
- `test_stop_flag.py` ✅ - Stop flag
- `test_templates_renderer.py` ✅ - Template rendering
- `test_use_cases.py` ✅ - Use case tests

## What's MISSING (Critical for Refactor):

### 1. CUA Browser Tests ❌
**File to create**: `tests/unit/test_openai_cua_browser.py`
```python
import pytest
from unittest.mock import Mock, patch

class TestOpenAICUABrowser:
    def test_uses_responses_api(self):
        """Test CUA uses Responses API not Agents SDK"""
        
    def test_screenshot_loop(self):
        """Test YOU provide browser, CUA analyzes"""
        
    def test_truncation_auto(self):
        """Test truncation='auto' is used"""
        
    def test_fallback_to_playwright(self):
        """Test fallback when CUA fails"""
```

### 2. UI/Streamlit Tests ❌
**File to create**: `tests/unit/test_ui_streamlit.py`
```python
class TestStreamlitUI:
    def test_three_input_mode(self):
        """Test 3-input panel renders"""
        
    def test_paste_mode_retained(self):
        """Test paste mode still works"""
        
    def test_decision_mode_selector(self):
        """Test mode selection UI"""
```

### 3. Autonomous Flow Tests ❌
**File to create**: `tests/integration/test_autonomous_flow.py`
```python
class TestAutonomousFlow:
    async def test_full_autonomous_flow(self):
        """Test browse → extract → evaluate → send"""
        
    async def test_respects_limit(self):
        """Test stops at profile limit"""
        
    async def test_mode_based_sending(self):
        """Test advisor/rubric/hybrid behaviors"""
```

### 4. DI Configuration Tests ❌
**File to create**: `tests/unit/test_di.py`
```python
class TestDI:
    def test_cua_browser_selection(self):
        """Test ENABLE_CUA selects right browser"""
        
    def test_decision_mode_selection(self):
        """Test mode selection logic"""
        
    def test_fallback_chain(self):
        """Test CUA → Playwright → Null"""
```

### 5. Decision Mode Tests ❌
**File to create**: `tests/unit/test_decision_modes.py`
```python
class TestDecisionModes:
    def test_advisor_no_auto_send(self):
        """Test advisor never auto-sends"""
        
    def test_rubric_always_auto_send(self):
        """Test rubric auto-sends on YES"""
        
    def test_hybrid_conditional_send(self):
        """Test hybrid uses confidence"""
```

## Test Coverage Summary:

| Component | Current Coverage | Needed |
|-----------|-----------------|---------|
| Core Logic | ✅ 90% | Good |
| CUA Browser | ❌ 0% | Critical |
| UI/Streamlit | ❌ 0% | Critical |
| Autonomous Flow | ❌ 0% | Critical |
| DI Config | ❌ 0% | Important |
| Decision Modes | ⚠️ 50% | Enhance |

## Testing Strategy for Refactor:

### Phase 1: Add CUA Tests FIRST
- Mock Responses API calls
- Test screenshot loop
- Test fallback behavior

### Phase 2: Test as You Refactor
- Write test for new behavior
- Refactor code
- Ensure test passes

### Phase 3: Integration Tests
- Test full autonomous flow
- Test mode switching
- Test UI interactions

### Phase 4: E2E Tests (Manual + Auto)
- Real CUA calls (expensive)
- Full UI flow
- Production scenarios

## Test Commands:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/yc_matcher --cov-report=html

# Run specific test
pytest tests/unit/test_openai_cua_browser.py -xvs

# Run only integration
pytest tests/integration/ -xvs
```

## Effort Estimate:
- **New test files**: 5
- **Total new tests**: ~30-40
- **Time**: 4-5 hours
- **Coverage target**: >80%