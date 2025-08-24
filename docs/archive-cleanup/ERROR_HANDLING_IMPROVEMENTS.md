# Error Handling & Debugging Improvements

## Problem: "Black Box" Skipping

The app was skipping all profiles with no visibility into why. Errors were being caught, logged to a file, but not shown in the UI. This made debugging nearly impossible.

## Root Cause

1. **GPT-5 Responses API parameter mismatch**: 
   - Used `response_format` (not supported)
   - Used `reasoning_effort` and `verbosity` (don't exist)
   - Used wrong token parameter name

2. **Silent error handling**:
   - Exceptions returned as fake "NO" decisions
   - Errors logged to events.jsonl but not shown in UI
   - Generic error messages with no detail

## Solutions Implemented

### 1. Fixed GPT-5 Responses API Parameters

```python
# BEFORE (BROKEN)
client.responses.create(
    model="gpt-5",
    response_format={"type": "json_object"},  # NOT SUPPORTED!
    reasoning_effort="medium",  # DOESN'T EXIST!
    max_completion_tokens=800,  # WRONG NAME!
)

# AFTER (WORKING)
client.responses.create(
    model="gpt-5",
    input=[...],
    max_output_tokens=800,  # CORRECT!
    # Request JSON in the prompt instead
)
```

### 2. Enhanced Error Visibility

**Decision Adapter**:
- Returns "ERROR" decision (not "NO") to distinguish failures
- Includes error type and details in response
- Logs comprehensive error information

**Autonomous Flow**:
- Handles ERROR decisions separately
- Adds errors to results for UI visibility
- Logs detailed error events

**UI (Streamlit)**:
- Shows error count in metrics
- Displays error details prominently
- Color-codes events by type (errors in red)

### 3. Added Retry & Recovery Mechanisms

```python
# New error_recovery.py module
retry = RetryWithBackoff(
    max_retries=3,
    initial_delay=2.0,
    backoff_factor=2.0,
)

# Automatic retry on API failures
resp = retry.execute(
    api_call_function,
    operation_name="gpt5_decision",
)
```

### 4. Debug Mode Configuration

```python
# config.py additions
def is_debug_mode() -> bool:
    return os.getenv("DEBUG_MODE", "0") == "1"

def get_log_level() -> str:
    return "DEBUG" if is_debug_mode() else "INFO"
```

### 5. Documentation Updates

- **GPT5_FACTS.md**: Updated with correct parameter names
- **GPT5_RESOLUTION_SUMMARY.md**: Documents the issue and fix
- **CLAUDE.md**: Added warnings about GPT-5 parameters

## Testing the Improvements

### 1. Enable Debug Mode
```bash
export DEBUG_MODE=1
export LOG_LEVEL=DEBUG
```

### 2. Watch for Errors in UI
- Error count in metrics
- Red error events in Recent Events
- Detailed error messages in expander

### 3. Check Events Log
```bash
tail -f .runs/events.jsonl | jq '.'
```

### 4. Test Error Recovery
The app now:
- Retries failed API calls up to 3 times
- Shows clear error messages
- Distinguishes between real "NO" and errors
- Continues processing after errors

## Key Takeaways

1. **Never hide errors** - Always surface them to the UI
2. **Distinguish error states** - ERROR vs NO decision
3. **Provide context** - Include error type, profile number, etc.
4. **Enable debugging** - Debug mode for detailed logging
5. **Retry on failure** - Transient errors shouldn't break the flow
6. **Document API quirks** - GPT-5 Responses API has different parameters

## Environment Variables for Debugging

```bash
# Enable all debugging features
export DEBUG_MODE=1
export LOG_LEVEL=DEBUG
export SHADOW_MODE=1  # Test without sending
export MAX_PROFILES=2  # Test with few profiles
```

## Monitoring Commands

```bash
# Watch events in real-time
tail -f .runs/events.jsonl | jq '.event'

# Count errors
grep "ERROR" .runs/events.jsonl | wc -l

# See detailed errors
jq 'select(.event == "evaluation_error")' .runs/events.jsonl
```

---

**Result**: The app now provides full visibility into errors, making debugging straightforward instead of a guessing game.
# DEPRECATED (December 2025)
This file is archived and may contain outdated OpenAI API guidance.
For the single source of truth, see `OPENAI_API_REFERENCE.md` and `CONTEXT7_TRUTH.md`.
Do not rely on this file for current parameters.
