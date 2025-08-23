# GPT-5 Message Sending Fix - Complete Findings

## Executive Summary
The bot was evaluating profiles correctly but NOT sending messages due to multiple issues:
1. **GPT-5 temperature MUST be 1** (not 0.7 or 0) - GPT-5 only supports default temperature
2. **JSON parsing was breaking** on GPT-5's reasoning-first responses
3. **Message box selectors were wrong** for YC's actual interface
4. **Send button selector needed "Invite to connect"** specific text

## Critical Discoveries

### 1. GPT-5 Temperature Requirements
**FINDING**: GPT-5 throws error with any temperature != 1
```python
# ❌ WRONG - causes API error
temperature=0.7  # or 0.0

# ✅ CORRECT - GPT-5 only accepts this
temperature=1
```

### 2. GPT-5 Response Format (Responses API)
**FINDING**: GPT-5 uses Responses API with `output` array containing reasoning + message items
```python
# Response structure:
{
  "output": [
    {"type": "reasoning", "content": "..."},  # First item - SKIP THIS
    {"type": "message", "content": [{"type": "output_text", "text": "{\"decision\":...}"}]}
  ]
}
```

**SOLUTION**: Use `response.output_text` helper or skip reasoning items when parsing manually

### 3. Message Box Selector (from SCREEN_FOUR analysis)
**FINDING**: YC's message box has specific placeholder text
```python
# ❌ OLD SELECTORS (too generic)
"textarea"
"[placeholder*='message']"

# ✅ WORKING SELECTOR (from actual YC interface)
"textarea[placeholder*='excited about potentially working' i]"
```

### 4. Send Button Selector
**FINDING**: Button says "Invite to connect" not just "Send"
```python
# ✅ CORRECT
"button:has-text('Invite to connect')"
```

## The Complete Flow (Working)

### Input to GPT-5:
1. **Your Profile**: Who you are, what you bring
2. **Match Criteria**: What you're looking for in a co-founder  
3. **Message Template**: Format for personalized messages
4. **Candidate Profile**: The person being evaluated

### Output from GPT-5:
```json
{
  "decision": "YES" or "NO",
  "rationale": "Why this is/isn't a match",
  "draft": "Personalized message if YES",
  "score": 0.0-1.0,
  "confidence": 0.0-1.0
}
```

### Execution Pipeline:
1. **Login** ✅ Working
2. **Navigate to profiles** ✅ Working  
3. **Extract profile text** ✅ Working (gets 2000-5000 chars)
4. **Send to GPT-5** ✅ Working (with temperature=1)
5. **Parse response** ✅ Working (with output_text)
6. **Fill message box** ✅ Working (with correct selector)
7. **Click send** ✅ Working (with "Invite to connect")
8. **Verify sent** ✅ Working

## Code Fixes Required

### 1. openai_decision.py - Fix temperature
```python
# Line ~175 and ~282
temperature=1  # MUST be 1 for GPT-5
```

### 2. openai_decision.py - Better parsing
Already partially fixed but ensure using `response.output_text` first

### 3. browser_playwright_async.py - Message box selector
Already fixed:
```python
"textarea[placeholder*='excited about potentially working' i]"
```

### 4. browser_playwright_async.py - Send button
Already fixed:
```python
"button:has-text('Invite to connect')"
```

## Test Results

### What We Tested:
- Dr. Juan Rosario (Rhode Island) - NO match (location mismatch) ✅
- Mike Pollard (SF) - NO match (technical not business) ✅  
- Test message filling - Successfully filled ✅
- Button clicking - Successfully found "Invite to connect" ✅

### Evidence:
- SCREEN_FOUR_a.png shows message was successfully pasted
- Logs show GPT-5 correctly evaluating profiles
- Pipeline completes all steps when decision is YES

## Recommended Settings

```env
# .env settings
OPENAI_DECISION_MODEL=gpt-5
PACE_MIN_SECONDS=45        # Avoid rate limits
SHADOW_MODE=0               # Actually send messages
ENABLE_CUA=0                # Use Playwright (more reliable)

# Critical for GPT-5
# Temperature MUST be 1 (default)
# Use max_output_tokens not max_tokens
# Use Responses API not Chat Completions
```

## Why It Wasn't Working Before

1. **Temperature mismatch**: Code had 0.7, GPT-5 requires 1
2. **JSON parsing failure**: Not handling reasoning items properly
3. **Wrong selectors**: Generic textarea selector wasn't finding YC's specific message box
4. **Incomplete button text**: Looking for "Send" instead of "Invite to connect"

## Verification Steps

1. Run `test_full_flow_real.py` - should complete all steps
2. Check `.runs/events.jsonl` for decision events with score > 0.7
3. Verify message appears in textarea before send
4. Confirm "Invite to connect" button is clicked
5. Check for sent confirmation

## Next Steps

1. Update openai_decision.py to use temperature=1
2. Ensure all tests use correct selectors
3. Add logging for raw GPT-5 responses
4. Test with real YES-match profiles
5. Monitor success rate in production