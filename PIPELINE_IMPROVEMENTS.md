# Pipeline Improvements: Systematic Fix Plan
*2025 Best Practices for Observable, Debuggable AI Workflows*

## Purpose
This document provides a **prioritized, actionable plan** to fix the observability and validation gaps identified in the YC Co-Founder Matcher pipeline.

Based on analysis in:
- `DATA_PIPELINE.md` - Complete pipeline documentation
- `AI_RESPONSE_OBSERVABILITY.md` - Current observability gaps

---

## Prioritization Framework

**Impact:** How much does this improve pipeline reliability?
**Effort:** How hard is it to implement?

```
Priority = Impact × (10 / Effort)

High Priority:   Score > 7
Medium Priority: Score 4-7
Low Priority:    Score < 4
```

---

## High Priority Fixes (Do First)

### 1. Add Correlation IDs for End-to-End Tracing
**Impact:** 10/10 - Enables debugging any issue
**Effort:** 2/10 - Simple UUID generation
**Priority Score:** 50

**Problem:**
- Cannot trace a profile through the pipeline
- Events are disconnected
- Profile numbers reset on restart

**Solution:**
```python
# In autonomous_flow.py, generate unique ID per profile
import uuid

profile_id = f"{hash_profile_text(profile_text)}_{uuid.uuid4().hex[:8]}"

# Add to ALL log events
logger.emit({
    "event": "...",
    "profile_id": profile_id,  # Add this everywhere
    "..."
})
```

**Files to Modify:**
- `src/yc_matcher/application/autonomous_flow.py` (generate ID)
- `src/yc_matcher/infrastructure/ai/openai_decision.py` (accept + log ID)
- `src/yc_matcher/application/use_cases.py` (pass through ID)

**Test:**
```bash
# After fix, grep events for specific profile_id
cat .runs/events.jsonl | grep "abc123_12345678"

# Should show: extracted → decision → sent (or skipped)
```

---

### 2. Log AI Request/Response Content
**Impact:** 10/10 - Enables auditing decisions
**Effort:** 3/10 - Add logging calls
**Priority Score:** 33

**Problem:**
- No record of what was sent to AI
- No record of raw AI response
- Cannot debug why AI made specific decision

**Solution:**
```python
# In openai_decision.py, after building prompt
logger.emit({
    "event": "ai_request",
    "profile_id": profile_id,
    "model": self.model,
    "prompt_tokens_est": len(user_text) // 4,  # Rough estimate
    "profile_excerpt": profile.raw_text[:200],  # First 200 chars
    "criteria_hash": hashlib.sha256(criteria.text.encode()).hexdigest()[:16],
    "timestamp": time.time()
})

# After receiving response
logger.emit({
    "event": "ai_response",
    "profile_id": profile_id,
    "model": self.model,
    "raw_content": content[:500],  # First 500 chars of response
    "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],
    "tokens_in": response.usage.input_tokens,
    "tokens_out": response.usage.output_tokens,
    "latency_ms": decision_ms,
    "timestamp": time.time()
})
```

**PII Protection:**
- Only log excerpts (first N chars)
- Hash full content for reference
- Don't log emails/phone numbers

**Files to Modify:**
- `src/yc_matcher/infrastructure/ai/openai_decision.py`

---

### 3. Log Draft Messages Before Sending
**Impact:** 9/10 - Audit trail for compliance
**Effort:** 2/10 - One log call
**Priority Score:** 45

**Problem:**
- No record of what messages were sent
- Cannot verify personalization
- Cannot detect spam patterns
- ⚠️ AI's original draft is lost (overwritten in `use_cases.py:30`)

**Solution:**
```python
# ⚠️ NOTE: draft here is TEMPLATE OUTPUT, not AI's original draft!
# The AI's draft was overwritten in use_cases.py before it gets here

# In autonomous_flow.py, before sending
if would_send and evaluation.get("decision") == "YES":
    draft = evaluation.get("draft", "")  # ← This is template output!
    if draft:
        # Log draft (with PII protection)
        logger.emit({
            "event": "message_prepared",
            "profile_id": profile_id,
            "draft_hash": hashlib.sha256(draft.encode()).hexdigest()[:16],
            "draft_length": len(draft),
            "draft_excerpt": draft[:100],  # First 100 chars
            # Check for template placeholders (square brackets, not braces!)
            "contains_template_vars": "[Name]" in draft or "[name]" in draft or "[" in draft,
            "timestamp": time.time()
        })

        if not shadow_mode:
            success = self.send(draft, 1)
```

**Additional Fix Needed:**
To log BOTH AI draft and template output, modify `use_cases.py:28-31`:
```python
def __call__(self, profile: Profile, criteria: Criteria) -> Mapping[str, Any]:
    data = self.decision.evaluate(profile, criteria)

    # ⚠️ Current code UNCONDITIONALLY overwrites draft
    # Store AI's original draft before overwriting
    ai_draft = data.get("draft", "")  # ← NEW: Preserve AI draft
    template_draft = self.message.render(data)  # ← Render template

    return {
        **data,
        "ai_draft": ai_draft,           # ← NEW: Keep AI draft
        "draft": template_draft         # ← Template for sending
    }
```

**Files to Modify:**
- `src/yc_matcher/application/autonomous_flow.py`

---

### 4. Add Semantic Validation Checks
**Impact:** 8/10 - Catch AI errors early
**Effort:** 5/10 - Requires NLP checks
**Priority Score:** 16

**Problem:**
- AI can return valid JSON but nonsense content
- No check if rationale is meaningful
- No check if draft is personalized
- No check if score/decision align

**Solution:**
```python
# In openai_decision.py, after schema validation
def _validate_semantic(payload: dict, profile_text: str) -> tuple[bool, list[str]]:
    """Semantic validation of AI response."""
    warnings = []

    # Check 1: Rationale is meaningful (not too short)
    if len(payload["rationale"]) < 20:
        warnings.append("rationale_too_short")

    # Check 2: Draft is personalized (if YES)
    if payload["decision"] == "YES":
        draft = payload["draft"]
        # Look for generic phrases
        generic_phrases = ["hi there", "hello", "dear candidate", "to whom it may concern"]
        if any(phrase in draft.lower() for phrase in generic_phrases):
            warnings.append("draft_not_personalized")

        # Check if draft mentions something from profile
        # (Simple check: any word > 5 chars from profile in draft)
        profile_words = {w for w in profile_text.split() if len(w) > 5}
        draft_words = {w for w in draft.split() if len(w) > 5}
        overlap = len(profile_words & draft_words)
        if overlap < 3:
            warnings.append("draft_no_profile_reference")

    # Check 3: Score and decision align
    score = payload["score"]
    decision = payload["decision"]
    if decision == "YES" and score < 0.5:
        warnings.append("score_decision_mismatch_low")
    elif decision == "NO" and score > 0.7:
        warnings.append("score_decision_mismatch_high")

    # Check 4: Confidence is reasonable
    confidence = payload["confidence"]
    if confidence < 0.3:
        warnings.append("confidence_very_low")

    return len(warnings) == 0, warnings

# Use it after schema validation
ok, err = _validate_decision(payload)
if ok:
    semantic_ok, warnings = _validate_semantic(payload, profile.raw_text)
    logger.emit({
        "event": "semantic_validation",
        "profile_id": profile_id,
        "passed": semantic_ok,
        "warnings": warnings
    })
```

**Files to Modify:**
- `src/yc_matcher/infrastructure/ai/openai_decision.py`

---

## Medium Priority Fixes (Do Second)

### 5. Store Profile Excerpts with Decisions
**Impact:** 7/10 - Enables decision auditing
**Effort:** 2/10 - Add field to events
**Priority Score:** 35

**Problem:**
- Decisions logged without profile context
- Cannot verify if decision matches profile

**Solution:**
```python
# In autonomous_flow.py, when logging decision
logger.emit({
    "event": "decision",
    "profile_id": profile_id,
    "profile_hash": profile_hash,
    "profile_excerpt": profile_text[:200],  # Add this
    "decision": evaluation.get("decision"),
    "rationale": evaluation.get("rationale"),
    "score": evaluation.get("score"),
    # ...
})
```

**Files to Modify:**
- `src/yc_matcher/application/autonomous_flow.py`

---

### 6. Add Validation Success Logging
**Impact:** 6/10 - Complete audit trail
**Effort:** 1/10 - One log call
**Priority Score:** 60

**Problem:**
- Only validation failures logged
- No visibility into successful responses

**Solution:**
```python
# In openai_decision.py, after validation
ok, err = _validate_decision(payload)
if not ok:
    # Existing failure logging
    logger.emit({"event": "validation_failure", ...})
else:
    # Add success logging
    logger.emit({
        "event": "validation_success",
        "profile_id": profile_id,
        "decision": payload["decision"],
        "score": payload["score"],
        "confidence": payload["confidence"],
        "draft_length": len(payload["draft"]),
        "timestamp": time.time()
    })
```

**Files to Modify:**
- `src/yc_matcher/infrastructure/ai/openai_decision.py`

---

### 7. Improve Error Context Logging
**Impact:** 7/10 - Better debugging
**Effort:** 3/10 - Capture more context
**Priority Score:** 23

**Problem:**
- Only error message logged
- No traceback
- No OpenAI request_id

**Solution:**
```python
# In openai_decision.py, exception handler
except Exception as e:
    import traceback
    import sys

    # Get full traceback
    tb = traceback.format_exc()

    # Try to get OpenAI request_id
    request_id = None
    if hasattr(e, "request_id"):
        request_id = e.request_id
    elif hasattr(e, "response") and hasattr(e.response, "headers"):
        request_id = e.response.headers.get("x-request-id")

    logger.emit({
        "event": "openai_error",
        "profile_id": profile_id,
        "error": str(e),
        "error_type": type(e).__name__,
        "traceback": tb,  # Add this
        "request_id": request_id,  # Add this
        "model": self.model,
        "profile_length": len(profile.raw_text),
        "criteria_length": len(criteria.text)
    })
```

**Files to Modify:**
- `src/yc_matcher/infrastructure/ai/openai_decision.py`

---

### 8. Add Profile Extraction Confidence Score
**Impact:** 6/10 - Catch bad extractions
**Effort:** 4/10 - Heuristic checks
**Priority Score:** 15

**Problem:**
- No validation that extracted text is a profile
- Could extract navigation, errors, ads

**Solution:**
```python
# In playwright_async.py, after extracting text
def _calculate_extraction_confidence(text: str) -> float:
    """Estimate if extracted text looks like a profile."""
    score = 0.0

    # Check length (profiles are usually 200-2000 chars)
    if 200 <= len(text) <= 2000:
        score += 0.3
    elif len(text) > 100:
        score += 0.1

    # Check for profile keywords
    keywords = ["experience", "background", "skills", "looking for", "interested in"]
    keyword_count = sum(1 for kw in keywords if kw.lower() in text.lower())
    score += keyword_count * 0.1

    # Check for navigation/error keywords (negative score)
    bad_keywords = ["sign in", "log out", "error", "404", "not found"]
    bad_count = sum(1 for kw in bad_keywords if kw.lower() in text.lower())
    score -= bad_count * 0.2

    # Check for structured data
    if "Name:" in text or "name:" in text:
        score += 0.2

    return max(0.0, min(1.0, score))

# After extraction
text = await elem.inner_text()
confidence = _calculate_extraction_confidence(text)

# Log confidence
logger.emit({
    "event": "profile_extracted",
    "profile_id": profile_id,
    "extracted_len": len(text),
    "confidence": confidence,  # Add this
    "text_excerpt": text[:200]
})

# Warn if low confidence
if confidence < 0.5:
    logger.emit({
        "event": "extraction_warning",
        "profile_id": profile_id,
        "reason": "low_confidence",
        "confidence": confidence
    })
```

**Files to Modify:**
- `src/yc_matcher/infrastructure/browser/playwright_async.py`
- `src/yc_matcher/application/autonomous_flow.py` (skip if confidence < threshold)

---

## Low Priority Fixes (Nice to Have)

### 9. Build Observability Dashboard
**Impact:** 8/10 - Easy inspection
**Effort:** 8/10 - Requires UI work
**Priority Score:** 10

**Problem:**
- Must manually read JSONL files
- Hard to find specific issues

**Solution:**
- Build Streamlit dashboard for `.runs/events.jsonl`
- Show recent decisions, errors, costs
- Filter by date, decision, profile_id

**Files to Create:**
- `src/yc_matcher/interface/web/observability_dashboard.py`

---

### 10. Add Request/Response Storage
**Impact:** 5/10 - Detailed debugging
**Effort:** 6/10 - Storage system
**Priority Score:** 8

**Problem:**
- Only excerpts logged
- Cannot see full prompts/responses

**Solution:**
- Store full requests/responses in SQLite
- Reference by hash in JSONL events
- Query for deep debugging

**Files to Create:**
- `src/yc_matcher/infrastructure/persistence/request_store.py`

---

## Implementation Roadmap

### Phase 1: Quick Wins (Week 1)
1. ✅ Add correlation IDs everywhere
2. ✅ Log validation success
3. ✅ Log draft messages before sending
4. ✅ Store profile excerpts with decisions

**Deliverable:** Full audit trail for decisions

### Phase 2: Content Validation (Week 2)
5. ✅ Log AI request/response content
6. ✅ Add semantic validation checks
7. ✅ Improve error context logging
8. ✅ Add extraction confidence scores

**Deliverable:** Catch AI/extraction errors early

### Phase 3: Observability Tooling (Week 3-4)
9. ✅ Build observability dashboard
10. ✅ Add request/response storage

**Deliverable:** Easy pipeline inspection

---

## How to Test Improvements

### Test 1: Trace a Profile End-to-End
```bash
# Run bot on 1 profile
make run  # Set max_profiles=1

# Extract all events for that profile
PROFILE_ID=$(cat .runs/events.jsonl | jq -r '.profile_id' | head -1)
cat .runs/events.jsonl | jq "select(.profile_id == \"$PROFILE_ID\")"

# Should see: extracted → ai_request → ai_response → decision → sent
```

### Test 2: Verify AI Response Logging
```bash
# Check ai_response events exist
cat .runs/events.jsonl | jq 'select(.event == "ai_response")'

# Should contain: raw_content, tokens, latency
```

### Test 3: Check Semantic Validation
```bash
# Look for semantic_validation events
cat .runs/events.jsonl | jq 'select(.event == "semantic_validation")'

# Should show: passed=true/false, warnings=[]
```

### Test 4: Audit Sent Messages
```bash
# Find all sent messages with drafts
cat .runs/events.jsonl | jq 'select(.event == "message_prepared")'

# Should show: draft_excerpt, draft_hash, personalization check
```

---

## Success Metrics

After implementing fixes, we should be able to:

1. **Trace any profile** from extraction → decision → send in < 1 minute
2. **Audit any decision** by seeing profile excerpt + AI reasoning
3. **Verify personalization** of all sent messages
4. **Detect AI errors** before sending (semantic validation)
5. **Debug failures** with full context (traceback, request_id)
6. **Monitor costs** in real-time (token usage per profile)

---

## Code Quality Standards

All improvements must:
- ✅ Include type hints
- ✅ Follow existing code style (ruff/mypy pass)
- ✅ Add docstrings for new functions
- ✅ Include unit tests (where applicable)
- ✅ Log PII-protected excerpts only (not full content)
- ✅ Use correlation IDs for tracing

---

## Additional Fixes Needed (Not Covered Above)

### Fix A: Cost Calculation Uses Wrong Rates
**File:** `src/yc_matcher/infrastructure/ai/openai_decision.py:76`

**Problem:**
```python
# ALWAYS uses GPT-4o rates regardless of model!
cost_est = (inp * 0.003 / 1000.0) + (out * 0.012 / 1000.0)
```

**Solution:**
```python
# Model-specific pricing
PRICING = {
    "gpt-4o": (0.003, 0.012),
    "gpt-4-turbo": (0.001, 0.004),
    "gpt-4": (0.03, 0.06),
    "gpt-5": (0.015, 0.06),
    "gpt-5-mini": (0.001, 0.004),
}

def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
    input_rate, output_rate = PRICING.get(model, (0.003, 0.012))  # Default to GPT-4o
    return (input_tokens * input_rate / 1000.0) + (output_tokens * output_rate / 1000.0)
```

### Fix B: Wire Up `your_profile` Input
**File:** `src/yc_matcher/application/autonomous_flow.py:206`

**Problem:**
- User's profile is collected but never used
- AI doesn't see the user's background
- `your_profile` is a parameter (line 59), NOT stored as `self.your_profile`

**Solution:**
```python
# In autonomous_flow.py:206
# BEFORE: evaluation = self.evaluate(profile, criteria_obj)
# AFTER: Pass your_profile parameter to evaluation
evaluation = self.evaluate(profile, criteria_obj, your_profile=your_profile)

# Update EvaluateProfile use case signature to accept your_profile
# Update openai_decision.py prompt to include your_profile in context
```

### Fix C: Wire Up `threshold` and `auto_send` UI Controls
**File:** `src/yc_matcher/interface/web/ui_streamlit.py:210-219`

**Problem:**
- UI shows threshold/auto_send controls but they're ignored
- Values never passed to flow

**Solution:**
```python
# In ui_streamlit.py
results = flow.run(
    your_profile=your_profile,
    criteria=criteria_text,
    template=template_text,
    mode="ai",
    limit=max_profiles,
    shadow_mode=shadow_mode,
    threshold=threshold,      # ← ADD THIS
    auto_send=auto_send,      # ← ADD THIS
)

# Update autonomous_flow.py to actually use these parameters
```

---

## Next Actions

1. **Review this plan** with team/stakeholders
2. **Prioritize** which fixes to implement first
3. **Create GitHub issues** for each fix
4. **Implement Phase 1** (quick wins)
5. **Test** with real YC profiles
6. **Iterate** based on findings

Ready to start coding? Begin with:
```bash
# Create feature branch
git checkout -b feature/observability-improvements

# Start with Fix #1: Correlation IDs
# Edit: src/yc_matcher/application/autonomous_flow.py
```
