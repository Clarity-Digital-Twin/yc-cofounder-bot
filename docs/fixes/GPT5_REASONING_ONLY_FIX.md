# GPT-5 Reasoning-Only Response Fix 🚨

## The Critical Issue We Missed

Despite extensive testing, our GPT-5 integration is failing in production with:
```
Could not extract text from GPT-5 response. Output items: 1, Types: ['reasoning']
```

## Root Cause Analysis

### Why Our Tests Passed But Production Failed

1. **Our Tests Were Wrong**
   ```python
   # In ALL our tests, we mocked like this:
   Mock(output_text='{"decision": "YES", ...}')  # <-- WRONG!
   ```
   We always assumed `output_text` would be populated with our JSON.

2. **Real GPT-5 Behaves Differently**
   ```python
   # Real GPT-5 Responses API returns:
   {
     "output": [
       {
         "type": "reasoning",  # <-- ONLY reasoning, no message!
         "content": "Let me analyze this profile..."
       }
     ],
     "output_text": ""  # <-- Empty or missing!
   }
   ```

3. **Our Code Skips Reasoning Items**
   ```python
   # In openai_decision.py lines 238-246:
   if item_type == "reasoning":
       # We just LOG and SKIP reasoning items!
       continue
   ```
   
4. **Result: Total Failure**
   - No message items → `text_parts` stays empty
   - Reasoning items skipped → no JSON extracted
   - Empty string → ValueError thrown
   - Bot can't evaluate ANY profiles

## Why This Happened

### Mocking vs Reality Gap
- **Mocked**: We assumed GPT-5 would always populate `output_text` or return message items
- **Reality**: GPT-5 often returns ONLY reasoning items, especially when thinking hard
- **Gap**: Our tests never simulated reasoning-only responses

### The SDK Misleads
The OpenAI SDK's `output_text` helper is supposed to aggregate all text, but:
- It might not include reasoning content
- It might be empty even when reasoning exists
- We can't rely on it alone

## The Comprehensive Fix

### 1. Add Verbosity Control (Nudge for Message Items)
```python
params = {
    "model": "gpt-5",
    "input": [...],
    "max_output_tokens": 800,
    "verbosity": "low",  # <-- Discourages verbose reasoning-only responses
}

try:
    r = client.responses.create(**params)
except Exception as e:
    # Remove optional params on 400 error
    params.pop("verbosity", None)
    params.pop("response_format", None)
    params.pop("temperature", None)
    r = client.responses.create(**params)
```

### 2. Add Reasoning-Only Rescue Parser
```python
def _extract_json_from_reasoning(reasoning_content: str) -> dict | None:
    """Extract JSON from reasoning trace when no message item exists."""
    # Look for JSON-like structure in reasoning
    import re
    json_pattern = r'\{[^{}]*"decision"[^{}]*\}'
    
    match = re.search(json_pattern, reasoning_content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None

# In the main parser:
if not c:  # No message content found
    # Try to rescue from reasoning items
    for item in r.output:
        if item.type == "reasoning" and hasattr(item, "content"):
            reasoning_text = str(item.content)
            
            # Try to extract JSON from reasoning
            rescued_json = _extract_json_from_reasoning(reasoning_text)
            if rescued_json:
                self.logger.emit({
                    "event": "gpt5_reasoning_rescue",
                    "rescued": True,
                    "json_keys": list(rescued_json.keys())
                })
                c = json.dumps(rescued_json)  # Convert back to string for parsing
                break
```

### 3. Strengthen System Prompt
```python
sys_prompt = '''You are evaluating profiles for co-founder matching.

CRITICAL: Your response MUST be a valid JSON object with these keys:
- decision: "YES" or "NO"  
- rationale: Brief explanation
- draft: Message to send (if YES)
- score: 0.0 to 1.0
- confidence: 0.0 to 1.0

DO NOT place the JSON in a reasoning trace.
DO NOT add any text before or after the JSON.
Your final message MUST contain ONLY the JSON object.'''
```

### 4. Add Comprehensive Telemetry
```python
self.logger.emit({
    "event": "gpt5_response_structure",
    "output_types": [item.type for item in r.output],
    "has_output_text": bool(r.output_text),
    "output_text_len": len(r.output_text) if r.output_text else 0,
    "has_message": any(item.type == "message" for item in r.output),
    "has_reasoning": any(item.type == "reasoning" for item in r.output),
    "reasoning_rescue_needed": not bool(c),
})
```

### 5. Fix Our Tests to Match Reality
```python
# Create REALISTIC mocks that match actual GPT-5 behavior:
def mock_reasoning_only_response():
    """Mock a reasoning-only response like real GPT-5."""
    return Mock(
        output=[
            Mock(
                type="reasoning",
                content="Analyzing profile... This looks like a match. "
                       '{"decision": "YES", "rationale": "Good fit", '
                       '"draft": "Hi!", "score": 0.8, "confidence": 0.9}'
            )
        ],
        output_text="",  # Empty!
        usage=Mock(input_tokens=100, output_tokens=50)
    )

# Test the reasoning rescue path:
def test_gpt5_reasoning_only_rescue():
    mock_client = Mock()
    mock_client.responses.create.return_value = mock_reasoning_only_response()
    
    adapter = OpenAIDecisionAdapter(mock_client, model="gpt-5")
    result = adapter.evaluate(profile, criteria)
    
    # Should successfully extract from reasoning!
    assert result["decision"] == "YES"
```

## Implementation Priority

1. **IMMEDIATE**: Add reasoning rescue parser (fixes current failures)
2. **NEXT**: Add verbosity="low" to reduce reasoning-only responses  
3. **THEN**: Update tests to use realistic mocks
4. **FINALLY**: Add telemetry to track patterns

## Key Lessons

### 1. Test Against Real API Behavior
- Don't just mock what you HOPE the API returns
- Mock what it ACTUALLY returns in production
- Include edge cases like reasoning-only responses

### 2. Never Skip Content Types
- Don't assume reasoning items are useless
- GPT-5 might put your JSON in reasoning
- Always have a fallback parser

### 3. Telemetry Is Critical
- Log EVERY response structure
- Track which parsing method succeeded
- Monitor for patterns over time

## The Fix in One Sentence

**Stop skipping reasoning items - parse JSON from them when message items are missing.**