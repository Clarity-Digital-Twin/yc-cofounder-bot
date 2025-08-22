# Systematic Debugging Strategy

## The Problem: Reactive Firefighting

We were stuck in a cycle:
1. Run app → See error → Fix error
2. Run app → See different error → Fix different error
3. Repeat endlessly...

This is unprofessional and wastes time. We need systematic testing BEFORE running the app.

## Professional Solution: Pre-Flight Checks

### 1. Systematic Test Suite

Created comprehensive test files:
- `test_gpt5_systematic.py` - Tests all GPT-5 response formats
- `test_decision_flow.py` - Tests complete evaluation flow
- `test_extraction_debug.py` - Debug response extraction
- `preflight_check.py` - Validates everything before running

### 2. Understanding GPT-5 Response Structure

**Discovery**: GPT-5 Responses API returns an array with 2 items:
```python
response.output = [
    ResponseReasoningItem(type='reasoning', ...),  # Index 0
    ResponseOutputMessage(type='message', ...)      # Index 1 - THIS HAS OUR TEXT!
]
```

The actual JSON is in: `response.output[1].content[0].text`

**Critical Fix**: Look for item with `type='message'`, not just first item.

### 3. Error Visibility Improvements

**Before**: Errors returned as fake "NO" decisions → invisible skipping
**After**: 
- Return "ERROR" decision type
- Show error count in UI metrics
- Display error details in red
- Include error type and message

### 4. Pre-Flight Check System

Run before starting the app:
```bash
PYTHONPATH=src uv run python -m yc_matcher.infrastructure.preflight_check
```

Checks:
- ✅ Environment variables
- ✅ OpenAI API connectivity
- ✅ GPT-5 model availability
- ✅ Decision flow works
- ✅ Directories exist
- ✅ Browser setup

### 5. Error Recovery Mechanisms

Added `error_recovery.py` with:
- **RetryWithBackoff**: 3 retries with exponential delay
- **CircuitBreaker**: Prevents cascading failures
- **Fallback patterns**: Graceful degradation

## Complete Fix Applied

### OpenAI Decision Adapter

```python
# FIXED: Correct extraction for GPT-5
if hasattr(r, 'output') and isinstance(r.output, list):
    for item in r.output:
        if getattr(item, 'type', None) == 'message':  # Find message item
            if hasattr(item, 'content') and item.content:
                for content_item in item.content:
                    if hasattr(content_item, 'text'):
                        c = content_item.text  # Extract JSON text
                        break
```

### Key Parameter Fixes

```python
# WRONG (causes errors)
client.responses.create(
    response_format={"type": "json_object"},  # NOT SUPPORTED
    reasoning_effort="medium",                # DOESN'T EXIST
    max_completion_tokens=800,                # WRONG NAME
)

# CORRECT (working)
client.responses.create(
    model="gpt-5",
    input=[...],
    max_output_tokens=800,  # Correct parameter name
    # Request JSON in prompt instead of response_format
)
```

## Testing Strategy

### Level 1: Unit Tests
```bash
# Test individual components
pytest tests/unit/test_openai_decision_adapter.py
```

### Level 2: Integration Tests
```bash
# Test decision flow
uv run python test_decision_flow.py
```

### Level 3: Pre-Flight Checks
```bash
# Validate everything before running
PYTHONPATH=src uv run python -m yc_matcher.infrastructure.preflight_check
```

### Level 4: Debug Mode
```bash
# Run with full logging
export DEBUG_MODE=1
make run
```

## Monitoring & Debugging

### Real-time Event Monitoring
```bash
tail -f .runs/events.jsonl | jq '.event'
```

### Error Analysis
```bash
# Count errors
jq 'select(.event == "evaluation_error")' .runs/events.jsonl | wc -l

# See error details
jq 'select(.decision == "ERROR")' .runs/events.jsonl
```

### Debug Environment
```bash
export DEBUG_MODE=1
export LOG_LEVEL=DEBUG
export SHADOW_MODE=1  # Test without sending
export MAX_PROFILES=2  # Test with few profiles
```

## Key Learnings

1. **Test systematically** - Don't wait for runtime errors
2. **Understand API responses** - GPT-5 has complex structure
3. **Make errors visible** - Never hide failures
4. **Pre-flight checks** - Validate before running
5. **Retry on failure** - Transient errors shouldn't break flow
6. **Document everything** - Future debugging is easier

## Current Status

✅ **WORKING**:
- GPT-5 evaluation with correct extraction
- Error visibility in UI
- Retry mechanism for resilience
- Pre-flight validation
- Debug mode for troubleshooting

## Quick Test Commands

```bash
# 1. Run pre-flight checks
PYTHONPATH=src uv run python -m yc_matcher.infrastructure.preflight_check

# 2. Test decision flow
uv run python test_decision_flow.py

# 3. Run app with debug
export DEBUG_MODE=1 && make run

# 4. Monitor events
tail -f .runs/events.jsonl | jq '.'
```

---

**Result**: Professional, systematic debugging instead of reactive firefighting. All errors are visible, recoverable, and testable BEFORE running the app.