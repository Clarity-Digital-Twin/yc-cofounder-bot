# AI Response Processing & Observability - CURRENT STATE
*As-is documentation for debugging and improvement*

## The Core Problem

**We send profile data to OpenAI API → Get decision back → Need to verify the entire chain works correctly**

This document maps EXACTLY how the AI response is processed currently, what we can observe, and what gaps exist.

---

## The AI Response Journey: Input → Processing → Output

### 1. What Goes INTO the AI

**File:** `openai_decision.py:89-125`

```python
# BUILD THE PROMPT
sys_prompt = """
You are an expert recruiter evaluating potential co-founder matches.
You MUST return a valid JSON object with these exact keys:
- decision: string 'YES' or 'NO'
- rationale: string explaining your reasoning in 1-2 sentences
- draft: if YES, a personalized message to the candidate (if NO, empty string)
- score: float between 0.0 and 1.0 indicating match strength
- confidence: float between 0.0 and 1.0 indicating your confidence
"""

user_text = f"""
MY CRITERIA:
{criteria_text}

CANDIDATE PROFILE:
{profile.raw_text}

Evaluate if this candidate matches my criteria.
If YES, write a personalized outreach message that references specific details.
"""

# ⚠️ NOTE: Template is extracted but NOT included in prompt!
# The AI generates a draft, but it's immediately overwritten with template output
```

**What We CAN Observe:**
- ❌ Input prompt text (NOT logged today - this is a gap!)
- ✅ Profile text length: `len(profile.raw_text)`
- ✅ Criteria text length: `len(criteria_text)`

**What We CANNOT Observe:**
- ❌ Whether the profile text is actually meaningful content
- ❌ If criteria is well-formed
- ❌ If template has valid placeholders
- ❌ Token count BEFORE API call (only after)

**Current Logging:**
```python
# NONE at input stage! Only logs usage AFTER response
```

---

### 2. The API Call Itself

**File:** `openai_decision.py:140-245` (GPT-5 pathway) or `openai_decision.py:397-411` (GPT-4 pathway)

#### GPT-4 Call (Most Common)
```python
response = client.chat.completions.create(
    model="gpt-4o",  # or gpt-4-turbo
    messages=[
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_text}
    ],
    temperature=0.3,
    max_tokens=800
)

# Extract content
content = response.choices[0].message.content
```

**What We CAN Observe:**
- ✅ Model name: `self.model`
- ✅ Response object exists
- ✅ Token usage: `response.usage.input_tokens`, `response.usage.output_tokens`
- ✅ Raw content string: `content`

**What We CANNOT Observe:**
- ❌ API latency (we calculate it but don't validate)
- ❌ If API call actually succeeded vs returned cached/default
- ❌ API rate limit status
- ❌ Whether response was truncated due to max_tokens

**Current Logging:**
```python
# Token usage logged AFTER parsing (line 486-496)
logger.emit({
    "event": "model_usage",
    "model": self.model,
    "tokens_in": inp,
    "tokens_out": out,
    "cost_est": round(cost_est, 6),
    "prompt_ver": self.prompt_ver,
    "rubric_ver": self.rubric_ver
})

# Latency logged separately (line 489-496)
logger.emit({
    "event": "decision_latency",
    "model": self.model,
    "latency_ms": decision_ms,
    "success": payload.get("decision") != "ERROR"
})
```

#### GPT-5 Call (If Using gpt-5 Models)
```python
# Much more complex with fallback logic
try:
    # Try with response_format
    params = {
        "model": self.model,
        "input": [...],
        "max_output_tokens": max_tokens,
        "temperature": temperature,
        "response_format": {"type": "json_schema", ...}
    }
    r = client.responses.create(**params)
except Exception as e:
    # Fallback: remove response_format
    params.pop("response_format", None)
    r = client.responses.create(**params)

# Extract from complex output structure
if hasattr(r, "output_text"):
    c = r.output_text  # Easy path
elif hasattr(r, "output"):
    # Manual parsing of output array
    for item in r.output:
        if item.type == "message":
            # Extract text from content
```

**What We CAN Observe:**
- ✅ Which fallback path was taken: `event: "response_format_fallback"`
- ✅ Output parsing method: `event: "gpt5_parse_method"`
- ✅ Token usage (same as GPT-4)

**What We CANNOT Observe:**
- ❌ Why the first attempt failed (only logs error string)
- ❌ If output contains reasoning that should be ignored
- ❌ If response_format actually enforced the schema

**Current Logging:**
```python
# Fallback logged (line 208-216)
logger.emit({
    "event": "response_format_fallback",
    "error": error_str,
    "model": self.model
})

# Parse method logged (line 253-265)
logger.emit({
    "event": "gpt5_parse_method",
    "method": "output_text",  # or "manual_iteration"
    "text_len": text_len
})
```

---

### 3. Response Parsing & Validation

**File:** `openai_decision.py:426-453`

```python
# Parse JSON from response
payload = json.loads(content)

# Validate against schema
ok, err = _validate_decision(payload)
payload["decision_json_ok"] = ok

if not ok:
    # Log validation failure
    logger.emit({
        "event": "gpt5_parse_failure",  # Misleading name, applies to both GPT-4/5
        "reason": err,
        "output_text_len": len(content or ""),
        "model": self.model
    })

    # Return ERROR decision
    payload = {
        "decision": "ERROR",
        "rationale": f"Invalid model JSON: {err}",
        "draft": "",
        "score": 0.0,
        "confidence": 0.0,
        "decision_json_ok": False
    }
```

#### Validation Function
**File:** `openai_decision.py:13-38`

```python
def _validate_decision(d: dict) -> tuple[bool, str | None]:
    # Check all keys present
    keys = ("decision", "rationale", "draft", "score", "confidence")
    if not all(k in d for k in keys):
        return False, "missing_keys"

    # Check decision value
    if d["decision"] not in ("YES", "NO", "ERROR"):
        return False, "bad_decision"

    # Check types
    if not isinstance(d["rationale"], str):
        return False, "bad_rationale"
    if not isinstance(d["draft"], str):
        return False, "bad_draft"

    # Check score range
    if not (isinstance(d["score"], (int, float)) and 0.0 <= d["score"] <= 1.0):
        return False, "bad_score"

    # Check confidence range
    if not (isinstance(d["confidence"], (int, float)) and 0.0 <= d["confidence"] <= 1.0):
        return False, "bad_confidence"

    # Check draft not empty for YES
    if d["decision"] == "YES" and not d["draft"].strip():
        return False, "empty_draft_for_yes"

    return True, None
```

**What We CAN Observe:**
- ✅ JSON parse success/failure
- ✅ Schema validation result: `decision_json_ok` flag
- ✅ Specific validation error: `reason` field
- ✅ Raw content length if validation fails

**What We CANNOT Observe:**
- ❌ If rationale makes logical sense (just checks it's a string)
- ❌ If draft actually references profile details (no semantic check)
- ❌ If score/confidence correlate with decision (YES should have high score)
- ❌ If the AI hallucinated information not in the profile

**Current Logging:**
```python
# Only logs if validation FAILS (line 433-441)
logger.emit({
    "event": "gpt5_parse_failure",
    "reason": err,
    "output_text_len": len(content or ""),
    "model": self.model
})

# Does NOT log if validation SUCCEEDS
# Success is implicit (no log event)
```

**🚨 CRITICAL GAP:** If validation succeeds, we have NO log entry showing what the AI actually returned!

---

### 4. Error Handling

**File:** `openai_decision.py:455-476`

```python
except Exception as e:
    # Log detailed error
    error_detail = {
        "event": "openai_error",
        "error": str(e),
        "error_type": type(e).__name__,
        "model": self.model,
        "profile_length": len(profile.raw_text),
        "criteria_length": len(criteria.text)
    }
    logger.emit(error_detail)

    # Return ERROR decision
    payload = {
        "decision": "ERROR",
        "rationale": f"OpenAI API Error ({type(e).__name__}): {str(e)[:200]}",
        "draft": "",
        "score": 0.0,
        "confidence": 0.0,
        "error": str(e),
        "error_type": type(e).__name__
    }
```

**What We CAN Observe:**
- ✅ Exception type and message
- ✅ Input lengths (profile, criteria)
- ✅ Model name

**What We CANNOT Observe:**
- ❌ Full exception traceback (only `str(e)`)
- ❌ Request ID from OpenAI (for support)
- ❌ Whether this is a transient error (retry-able) vs permanent
- ❌ Rate limit vs auth vs content policy error

**Current Logging:**
```python
# Error logged (line 457-465)
logger.emit({
    "event": "openai_error",
    "error": str(e),
    "error_type": type(e).__name__,
    "model": self.model,
    "profile_length": len(profile.raw_text),
    "criteria_length": len(criteria.text)
})
```

---

### 5. Return Value & Downstream Usage

**File:** `openai_decision.py:478-498`

```python
# Add latency to payload
decision_ms = int((time.time() - decision_start) * 1000)
payload["latency_ms"] = decision_ms

# Stamp versions
payload.setdefault("prompt_ver", self.prompt_ver)
payload.setdefault("rubric_ver", self.rubric_ver)

# Log usage if present
if logger and "resp" in locals():
    self._log_usage(resp)
    logger.emit({
        "event": "decision_latency",
        "model": self.model,
        "latency_ms": decision_ms,
        "success": payload.get("decision") != "ERROR"
    })

return dict(payload)
```

**Returned Payload Structure:**
```python
{
    "decision": "YES" | "NO" | "ERROR",
    "rationale": "...",
    "draft": "...",
    "score": 0.85,
    "confidence": 0.75,
    "decision_json_ok": True,
    "latency_ms": 1234,
    "prompt_ver": "v1",
    "rubric_ver": "v1",
    # If error occurred:
    "error": "...",
    "error_type": "..."
}
```

**What We CAN Observe:**
- ✅ Decision value
- ✅ All fields in payload
- ✅ Latency measurement

**What We CANNOT Observe:**
- ❌ If decision aligns with actual profile content
- ❌ If rationale justifies the decision (semantic check)
- ❌ If draft message is actually personalized

**⚠️ CRITICAL:** The `draft` field in the returned payload is **NOT what the AI wrote**!

After this function returns, in `use_cases.py:28-31`:
```python
result = self._decision.evaluate(profile, criteria)

if result.get("decision") == "YES":
    # AI draft is DISCARDED and replaced with template output
    result["draft"] = self._message.render()  # ← Template replaces AI draft
```

**The AI generates a draft message, but it's immediately overwritten with the template renderer output.**

---

## How the Response is Used Downstream

### In AutonomousFlow (autonomous_flow.py)

**File:** `autonomous_flow.py:206-256`

```python
# Evaluate profile
evaluation = self.evaluate(profile, criteria_obj)

# Check for evaluation errors
if evaluation.get("decision") == "ERROR":
    error_msg = evaluation.get("error", "Unknown error")
    logger.emit({
        "event": "evaluation_error",
        "profile": i,
        "error": error_msg,
        "error_type": evaluation.get("error_type", "Unknown"),
        "rationale": evaluation.get("rationale", ""),
        "skip_reason": f"Decision error: {error_msg[:100]}"
    })
    # Skip to next profile
    browser.skip()
    continue

# Log decision event (only for successful evaluations)
logger.emit({
    "event": "decision",
    "profile": i,
    "decision": evaluation.get("decision"),
    "mode": mode,
    "rationale": evaluation.get("rationale", ""),
    "score": evaluation.get("score"),
    "auto_send": evaluation.get("auto_send", False),
    "decision_json_ok": evaluation.get("decision_json_ok", False)
})

# Send message if YES
if evaluation.get("decision") == "YES":
    draft = evaluation.get("draft", "")
    if draft and not shadow_mode:
        success = self.send(draft, 1)
        if success:
            logger.emit({
                "event": "sent",
                "profile": i,
                "ok": True,
                "mode": "auto",
                "verified": True
            })
```

**What We CAN Observe:**
- ✅ Decision logged for each profile
- ✅ Whether message was sent
- ✅ Error vs normal flow separation

**What We CANNOT Observe:**
- ❌ The actual draft message that was sent (NOT logged!)
- ❌ The AI's original draft (discarded before send)
- ❌ Correlation between decision and profile content
- ❌ If "verified: True" actually means verified or just assumed

**🚨 CRITICAL GAPS:**
1. **Draft message not logged** - We log that we sent, but not WHAT we sent
   - The `draft` in `evaluation` is the **template output**, NOT the AI's draft
   - AI's original draft is lost (overwritten in `use_cases.py:30`)
2. **Profile content not logged with decision** - Can't audit decisions
3. **No correlation ID** - Can't trace a specific profile through the pipeline

---

## Current Observability: What We Have

### Events in `.runs/events.jsonl`

#### 1. Model Usage Event
```json
{
  "event": "model_usage",
  "model": "gpt-4o",
  "tokens_in": 1234,
  "tokens_out": 156,
  "cost_est": 0.0054,
  "prompt_ver": "v1",
  "rubric_ver": "v1",
  "timestamp": "2025-10-12T14:23:45.123Z"
}
```

**Good:** Cost tracking
**Missing:** Request/response content

#### 2. Decision Event
```json
{
  "event": "decision",
  "profile": 0,
  "decision": "YES",
  "mode": "ai",
  "rationale": "Strong ML background, local to SF",
  "score": 0.85,
  "auto_send": false,
  "decision_json_ok": true,
  "engine": "playwright",
  "extracted_len": 1234
}
```

**Good:** Decision outcome, score, validation status
**Missing:** Draft message, profile hash, full AI response

#### 3. Sent Event
```json
{
  "event": "sent",
  "profile": 0,
  "ok": true,
  "mode": "auto",
  "verified": true
}
```

**Good:** Confirmation sent
**Missing:** Message content, recipient info, actual verification proof

#### 4. Error Events
```json
{
  "event": "openai_error",
  "error": "Rate limit exceeded",
  "error_type": "RateLimitError",
  "model": "gpt-4o",
  "profile_length": 1234,
  "criteria_length": 500
}
```

**Good:** Error capture
**Missing:** Request ID, retry status, traceback

---

## Observability Gaps - THE PROBLEMS

### 🚨 Gap 1: No Request/Response Audit Trail
**Problem:** We log that AI was called, but NOT what was sent or received

**Impact:** Cannot debug why AI made a specific decision

**Example:**
- AI says "YES" with rationale "Strong ML background"
- Profile actually said "No technical experience"
- We have NO WAY to detect this mismatch!

**Current Code:**
```python
# We log usage...
logger.emit({"event": "model_usage", "tokens_in": 1234, ...})

# But NOT the actual request/response!
# Missing: logger.emit({"event": "ai_request", "prompt": user_text, ...})
# Missing: logger.emit({"event": "ai_response", "content": content, ...})
```

### 🚨 Gap 2: No Correlation Between Profile & Decision
**Problem:** Profile text is extracted but not stored with decision

**Impact:** Cannot audit if decisions match profiles

**Current Code:**
```python
# Profile extracted
profile_text = browser.read_profile_text()
logger.emit({"event": "profile_extracted", "extracted_len": len(profile_text)})

# Decision made
evaluation = self.evaluate(profile, criteria_obj)
logger.emit({"event": "decision", "decision": "YES", ...})

# But NO connection between them!
# Missing: profile_hash, profile_excerpt in decision event
```

### 🚨 Gap 3: Draft Messages Not Logged
**Problem:** We send messages but don't log what was sent

**Impact:** Cannot verify personalization, cannot detect spam-like messages

**Current Code:**
```python
if evaluation.get("decision") == "YES":
    draft = evaluation.get("draft", "")
    if draft:
        success = self.send(draft, 1)
        logger.emit({"event": "sent", "ok": True})  # ❌ No draft logged!
```

### 🚨 Gap 4: Validation Success Not Logged
**Problem:** We only log when validation FAILS, not when it succeeds

**Impact:** Cannot see successful AI responses, only errors

**Current Code:**
```python
ok, err = _validate_decision(payload)
if not ok:
    logger.emit({"event": "gpt5_parse_failure", "reason": err})
    # Return ERROR
else:
    # ❌ NO LOG EVENT - just silently succeeds
    payload["decision_json_ok"] = True
```

### 🚨 Gap 5: No Semantic Validation
**Problem:** We check JSON schema but not content quality

**Impact:** AI can return nonsense that passes validation

**Examples of Valid-but-Wrong:**
- Rationale: "Good match" (no actual reasoning)
- Draft: "Hi there!" (not personalized)
- Score: 0.9 for Decision: "NO" (conflicting)

**Current Code:**
```python
# Only checks types and ranges
if not isinstance(d["rationale"], str):
    return False, "bad_rationale"

# ❌ No check: Is rationale meaningful?
# ❌ No check: Does draft reference profile?
# ❌ No check: Do score and decision align?
```

### 🚨 Gap 6: No End-to-End Tracing
**Problem:** Cannot trace a single profile through the entire pipeline

**Impact:** Debugging requires manual correlation of events

**Missing:**
- Correlation ID (profile_id, request_id)
- Timestamps on all events
- Start/end markers for each profile

**Current Code:**
```python
# Events have profile number but not a unique ID
logger.emit({"event": "decision", "profile": 0, ...})  # profile 0
logger.emit({"event": "sent", "profile": 0, ...})      # Which profile 0?

# If loop restarts, profile numbers reset!
```

---

## What SHOULD Be Observable (2025 Best Practices)

### 1. Full Request/Response Logging
```json
{
  "event": "ai_request",
  "profile_id": "abc123",
  "model": "gpt-4o",
  "prompt_hash": "def456",
  "profile_excerpt": "John Doe, ML Engineer, SF...",
  "criteria_hash": "xyz789",
  "timestamp": "2025-10-12T14:23:45.123Z"
}

{
  "event": "ai_response",
  "profile_id": "abc123",
  "model": "gpt-4o",
  "raw_content": "{\"decision\": \"YES\", ...}",
  "parsed_decision": "YES",
  "parsed_score": 0.85,
  "validation_result": "PASS",
  "tokens_in": 1234,
  "tokens_out": 156,
  "latency_ms": 1234,
  "timestamp": "2025-10-12T14:23:46.357Z"
}
```

### 2. Correlation IDs
```python
# Generate unique ID per profile
profile_id = f"{hash_profile_text(text)}_{int(time.time())}"

# Include in ALL events
logger.emit({"event": "...", "profile_id": profile_id, ...})
```

### 3. Content Validation Events
```json
{
  "event": "decision_validation",
  "profile_id": "abc123",
  "checks": {
    "schema_valid": true,
    "rationale_meaningful": true,      // NEW
    "draft_personalized": true,        // NEW
    "score_decision_aligned": true,    // NEW
    "draft_references_profile": true   // NEW
  }
}
```

### 4. Draft Message Logging (with PII protection)
```json
{
  "event": "message_sent",
  "profile_id": "abc123",
  "draft_hash": "sha256(...)",
  "draft_length": 234,
  "draft_excerpt": "Hi [NAME], I noticed you...",  // First 100 chars
  "personalization_score": 0.8,  // How personalized?
  "verified": true
}
```

### 5. Profile Content Logging (with PII protection)
```json
{
  "event": "profile_extracted",
  "profile_id": "abc123",
  "profile_hash": "def456",
  "extracted_len": 1234,
  "profile_excerpt": "Name: [REDACTED]\nSkills: Python, ML...",
  "extraction_method": "playwright",
  "confidence": 0.9  // How confident text is actually a profile?
}
```

---

## Summary: Current vs Desired State

| Aspect | Current State | Desired State |
|--------|--------------|---------------|
| **AI Request** | Not logged | Full prompt logged (with hashing) |
| **AI Response** | Only tokens logged | Full response + parsing details |
| **Validation** | Only failures logged | Success AND failures with details |
| **Draft Messages** | Not logged | Logged with PII protection |
| **Profile Content** | Length only | Hash + excerpt + confidence |
| **Correlation** | Profile number (resets) | Unique profile_id across events |
| **Semantic Checks** | None | Rationale, personalization, alignment |
| **Error Context** | Basic error string | Full traceback + request_id |
| **Tracing** | Manual correlation | Automatic via correlation_id |
| **Observability UI** | Read JSONL manually | Structured dashboard/queries |

---

## Next Steps: How to Fix This

1. **Add AI request/response logging** (capture full context)
2. **Implement correlation IDs** (trace profiles end-to-end)
3. **Add semantic validation** (check content quality, not just schema)
4. **Log draft messages** (with PII protection)
5. **Store profile excerpts** (for audit trail)
6. **Build observability queries** (easy way to inspect pipeline)

See: `PIPELINE_IMPROVEMENTS.md` (to be created next)
