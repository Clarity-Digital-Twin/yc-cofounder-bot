# Test Failures Analysis & Fix Plan

## Current Status
- Total tests: ~88
- Passing: ~72
- Failing: 16
- Categories: 5 distinct issue types

## Issue Categories

### 1. Async/Sync Mismatch (3 failures)
**Files:** `test_openai_cua_browser.py`
**Root Cause:** Tests trying to `await` sync methods or `asyncio.run()` in existing event loop

#### Failures:
- `test_browser_port_methods_use_cua_loop` - Awaiting sync `read_profile_text()`
- `test_fallback_to_playwright_when_cua_fails` - Awaiting sync `open()`
- `test_verify_sent_strict_checking` - Awaiting sync `verify_sent()`

**Fix Strategy:** 
- Tests should call sync methods without await
- OR create async test adapter wrapper

### 2. Decision Mode Assertions (2 failures)
**Files:** `test_decision_modes.py`
**Root Cause:** Test expectations don't match actual implementation

#### Failures:
- `test_hybrid_gates_with_rubric_first` - Expects "Score below threshold" but gets "Below threshold or red flags"
- `test_hybrid_includes_both_scores` - Expects "score" key but not present in result

**Fix Strategy:**
- Update test assertions to match actual implementation
- OR fix implementation to match expected behavior

### 3. DI Module Issues (3 failures)
**Files:** `test_di.py`
**Root Cause:** Missing imports/attributes after refactoring

#### Failures:
- `test_openai_adapter_when_enabled` - No `OpenAIDecisionAdapter` in di module
- `test_build_services_creates_logger_with_versions` - Logger missing `prompt_ver` attribute
- `test_cua_browser_when_enabled` - No `OpenAICUABrowser` in di module

**Fix Strategy:**
- Fix import paths in tests
- Ensure logger has expected attributes

### 4. UI/Streamlit Context Manager (8 failures)
**Files:** `test_ui_streamlit.py`
**Root Cause:** Mock columns don't support context manager protocol

#### All failures at line 39: `with col1:`
- Mock object doesn't support `__enter__` and `__exit__`

**Fix Strategy:**
- Make column mocks proper context managers
- Use MagicMock with spec or implement context protocol

### 5. Warnings
- `RuntimeWarning: coroutine was never awaited` - Need to properly handle async mocks

## Fix Priority Order
1. UI tests (8 failures) - Single root cause, high impact
2. Async/sync tests (3 failures) - Clear fix path
3. DI tests (3 failures) - Import/attribute fixes
4. Decision mode tests (2 failures) - Assertion updates
5. Warnings cleanup

## Quality Checks Needed
- `make lint` - Code formatting and style
- `make type` - Type checking with mypy
- `make test` - All unit tests
- `make verify` - Full CI validation