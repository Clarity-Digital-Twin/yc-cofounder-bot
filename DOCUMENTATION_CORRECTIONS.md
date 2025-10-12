# Documentation Corrections Report
*Generated: 2025-10-12*
*Based on deep code review vs documentation claims*

## Executive Summary

The three pipeline documentation files (`DATA_PIPELINE.md`, `AI_RESPONSE_OBSERVABILITY.md`, `PIPELINE_IMPROVEMENTS.md`) contain **10 major discrepancies** with the actual codebase. This document catalogs every error found and provides the correct behavior based on source code analysis.

**Status:** ❌ Documents are NOT ready for implementation
**Action Required:** Revise all three documents before implementing any fixes

---

## Critical Discrepancies Found

### 1. Your Profile Input is NEVER Used
**Claimed:** `DATA_PIPELINE.md:38-41`
> "User's profile description. Used by AI to evaluate match compatibility"

**Reality:** `autonomous_flow.py:59-336`
```python
def run(
    self,
    your_profile: str,  # Parameter exists
    criteria: str,
    template: str,
    # ...
) -> dict[str, Any]:
    # your_profile is NEVER passed to evaluate()!
    # Line 206: evaluation = self.evaluate(profile, criteria_obj)
    # Only passes candidate profile + criteria, NOT your_profile
```

**Impact:** User's background is collected but ignored. AI never sees it.

**Fix Needed:**
- Update docs to reflect that `your_profile` is currently unused
- OR update code to actually pass `your_profile` to AI prompt

---

### 2. Auto-Send and Threshold Parameters Are NOT Wired Up
**Claimed:** `DATA_PIPELINE.md:54-58`
> "auto_send: bool = True - Auto-send if match score > threshold"
> "threshold: float = 0.72 - Auto-send score threshold"

**Reality:** `ui_streamlit.py:210-219`
```python
# User can set auto_send and threshold in UI
auto_send = st.checkbox("Auto-send messages", value=True)
# But these are NEVER passed to the flow!

results = flow.run(
    your_profile=your_profile,
    criteria=criteria_text,
    template=template_text,
    mode="ai",
    limit=max_profiles,
    shadow_mode=shadow_mode,
    # threshold NOT passed!
    # auto_send NOT passed!
)
```

**Reality:** `autonomous_flow.py:256`
```python
# Hard-coded threshold in _should_auto_send
would_send = self._should_auto_send(dict(evaluation), mode, False, threshold)
# But threshold parameter here defaults to 0.7 (from function signature line 66)
# UI value is ignored!
```

**Impact:** User controls in UI do nothing. Pipeline always uses default threshold.

**Fix Needed:**
- Remove claims about configurable auto-send/threshold
- OR wire up UI parameters to actually flow to the decision logic

---

### 3. Quota Management Default is WRONG
**Claimed:** `DATA_PIPELINE.md:136-138`
> "quota = SQLiteDailyWeeklyQuota(Path('.runs/quota.sqlite'))"

**Reality:** `di.py:79-84`
```python
# Quota: calendar-aware (daily/weekly) if enabled, else simple file counter
quota = (
    SQLiteDailyWeeklyQuota(Path(".runs/quota.sqlite"))
    if config.is_calendar_quota_enabled()  # ← Must be explicitly enabled!
    else FileQuota()  # ← This is the default
)
```

**Impact:** Docs claim SQLite quota is always used. Actually defaults to FileQuota.

**Fix Needed:**
- Document that SQLite quota requires `ENABLE_CALENDAR_QUOTA=1` env var
- Show FileQuota as default

---

### 4. ensure_logged_in() Method Doesn't Exist
**Claimed:** `DATA_PIPELINE.md:167-168`
> "self.browser.ensure_logged_in()"

**Reality:** `autonomous_flow.py:101-119`
```python
# Check if already logged in or can auto-login
if hasattr(self.browser, "is_logged_in"):
    if not self.browser.is_logged_in():
        if has_credentials and hasattr(self.browser, "ensure_logged_in"):  # ← Check if method exists
            # Only calls if method exists
            self.browser.ensure_logged_in()
```

**Reality:** `playwright_async.py`
- No `ensure_logged_in()` method defined
- Only has `_auto_login_if_needed()` which is called internally from `open()`

**Impact:** Documented login flow doesn't match Playwright adapter

**Fix Needed:**
- Document actual login flow: `open()` → `_auto_login_if_needed()` internally
- Remove claims about `ensure_logged_in()` method

---

### 5. Message Template is NOT in the AI Prompt
**Claimed:** `DATA_PIPELINE.md:229-244` and `AI_RESPONSE_OBSERVABILITY.md:33-48`
> "MESSAGE TEMPLATE (use this style but personalize it): {template}"
> "Template for personalized outreach"

**Reality:** `use_cases.py:21-31`
```python
class EvaluateProfile:
    def __init__(
        self,
        decision: DecisionPort,
        message: TemplateRenderer  # ← Template renderer stored here
    ) -> None:
        self._decision = decision
        self._message = message

    def __call__(self, profile: Profile, criteria: Criteria) -> Mapping[str, Any]:
        # Get AI decision
        result = self._decision.evaluate(profile, criteria)

        # OVERRIDE the AI's draft with template-rendered message
        if result.get("decision") == "YES":
            result["draft"] = self._message.render()  # ← Template applied AFTER AI
```

**Reality:** `openai_decision.py:89-125`
```python
# Extract template from criteria if present
if "\nMessage Template:" in criteria.text:
    parts = criteria.text.split("\nMessage Template:")
    criteria_text = parts[0]
    template = parts[1].strip()
else:
    criteria_text = criteria.text

# But this template is NEVER used!
# It's extracted but not added to the prompt
```

**Impact:**
- AI never sees the template
- AI generates a draft that is immediately discarded
- Template renderer creates the actual message (not AI)

**Fix Needed:**
- Document that template is applied POST-AI decision
- Clarify that AI draft is overwritten by template
- Update prompt flow to show template is NOT in AI input

---

### 6. GPT-5 Parameter Defaults Are WRONG
**Claimed:** `DATA_PIPELINE.md:302-304` and `DATA_PIPELINE.md:810-812`
> "max_output_tokens=800"
> "temperature=1.0"

**Reality:** `config.py:193-205`
```python
def get_gpt5_max_tokens() -> int:
    return int(os.getenv("GPT5_MAX_TOKENS", "4000"))  # ← Default 4000, not 800

def get_gpt5_temperature() -> float:
    return float(os.getenv("GPT5_TEMPERATURE", "0.3"))  # ← Default 0.3, not 1.0
```

**Reality:** `openai_decision.py:145-149`
```python
max_tokens = config.get_gpt5_max_tokens() if self.model.startswith("gpt-5") else 800
temperature = config.get_gpt5_temperature() if self.model.startswith("gpt-5") else 0.3
```

**Impact:** Documented defaults don't match config defaults

**Fix Needed:**
- Update GPT-5 defaults to 4000 tokens, 0.3 temperature
- Note these are configurable via env vars

---

### 7. Cost Calculation Always Uses GPT-4o Rates
**Claimed:** `DATA_PIPELINE.md:744-764`
> "Cost (GPT-4o): ... Cost (GPT-4-turbo): ... Cost (GPT-5): ..."

**Reality:** `openai_decision.py:70-77`
```python
def _log_usage(self, resp: Any) -> None:
    # ...
    inp = int(getattr(usage, "input_tokens", 0) or 0) if usage else 0
    out = int(getattr(usage, "output_tokens", 0) or 0) if usage else 0

    # ALWAYS uses GPT-4o rates regardless of model!
    cost_est = (inp * 0.003 / 1000.0) + (out * 0.012 / 1000.0) if (inp or out) else 0.0

    self.logger.emit({
        "event": "model_usage",
        "model": self.model,  # ← Logs correct model
        "cost_est": round(cost_est, 6),  # ← But uses wrong rates!
    })
```

**Impact:** Cost estimates are wrong for all non-GPT-4o models

**Fix Needed:**
- Document that cost calculation uses GPT-4o rates only
- OR implement model-specific pricing lookup
- Note that actual costs will differ from estimates

---

### 8. Template Placeholders Use [Brackets] Not {Braces}
**Claimed:** `PIPELINE_IMPROVEMENTS.md:127-140`
> "contains_template_vars": "{{" in draft or "{name}" in draft"

**Reality:** `templates.py:15-32`
```python
class TemplateRenderer:
    def render(
        self,
        name: str | None = None,
        location: str | None = None,
        # ...
    ) -> str:
        txt = self._template
        # Replace [Name] with actual name
        txt = txt.replace("[Name]", name or "there")
        txt = txt.replace("[name]", name or "there")
        # Uses [Brackets] not {Braces}!
```

**Impact:** Proposed personalization check would always fail

**Fix Needed:**
- Update improvement plan to check for `[Name]`, `[project]`, etc.
- Not `{name}` or `{{name}}`

---

### 9. AI Draft is Overwritten, Not Sent
**Claimed:** `PIPELINE_IMPROVEMENTS.md:127-146`
> "draft = evaluation.get('draft', '') - Log the AI-generated draft"

**Reality:** `use_cases.py:28-31`
```python
def __call__(self, profile: Profile, criteria: Criteria) -> Mapping[str, Any]:
    result = self._decision.evaluate(profile, criteria)

    if result.get("decision") == "YES":
        # OVERWRITE AI draft with template
        result["draft"] = self._message.render()

    return result
```

**Impact:**
- `evaluation["draft"]` is NOT the AI-generated text
- It's the template-rendered message
- Logging this draft won't show what AI actually wrote

**Fix Needed:**
- Store original AI draft separately before overwriting
- OR document that draft is template output, not AI output
- Update improvement plan to log both AI draft and template output

---

### 10. No Prompt/Profile Logging Exists Today
**Claimed:** `AI_RESPONSE_OBSERVABILITY.md:33-48`
> "full prompt text is logged"

**Reality:** `openai_decision.py:89-340`
```python
# Prompt is built (lines 101-125)
sys_prompt = "..."
user_text = f"MY CRITERIA:\n{criteria_text}\n\nCANDIDATE PROFILE:\n{profile.raw_text}"

# API is called (lines 142-245 GPT-5, 397-411 GPT-4)
response = client.chat.completions.create(...)

# But NO logging of prompt or profile anywhere!
# Only logs token usage AFTER the fact
```

**Impact:** Claim that prompts are logged is false

**Fix Needed:**
- Document that NO prompt logging exists today
- This is a gap that needs to be implemented (not current state)

---

## Additional Issues

### 11. Threshold is Hard-Coded
**Reality:** `autonomous_flow.py:66`
```python
def run(
    self,
    # ...
    threshold: float = 0.7,  # ← Default 0.7 (not 0.72 as claimed)
    # ...
)
```

### 12. Profile Text Extraction Has No Confidence Scoring
**Reality:** `playwright_async.py:298-385`
- Just extracts text and returns it
- No confidence calculation
- No validation that it's a profile

---

## Summary of Required Changes

### DATA_PIPELINE.md Fixes:
1. ✅ Remove or mark `your_profile` as "currently unused"
2. ✅ Remove auto_send/threshold as configurable (they're hard-coded)
3. ✅ Document FileQuota as default, SQLite as optional
4. ✅ Fix login flow (no ensure_logged_in method)
5. ✅ Remove template from AI prompt section
6. ✅ Document that template is applied AFTER AI decision
7. ✅ Fix GPT-5 defaults (4000 tokens, 0.3 temp)
8. ✅ Fix cost calculations (all use GPT-4o rates)
9. ✅ Note threshold defaults to 0.7 (not 0.72)

### AI_RESPONSE_OBSERVABILITY.md Fixes:
1. ✅ Remove claim that template is in prompt
2. ✅ Document that NO prompt logging exists today
3. ✅ Clarify that draft in events is template output, not AI output
4. ✅ Update gaps to reflect actual missing features (not claimed features)

### PIPELINE_IMPROVEMENTS.md Fixes:
1. ✅ Fix template placeholder check ([Name] not {name})
2. ✅ Update draft logging to distinguish AI vs template output
3. ✅ Add note about your_profile being unused
4. ✅ Remove assumptions about configurable threshold
5. ✅ Add fix for cost calculation (model-specific rates)

---

## Decision Points for User

Before revising docs, we need to decide:

### Option A: Document Current Reality (Recommended First)
- Update all docs to match actual code behavior
- Mark unused features as "NOT IMPLEMENTED"
- Note gaps between UI and backend
- Implement fixes later

### Option B: Fix Code to Match Docs
- Wire up `your_profile` to AI prompt
- Wire up `auto_send`/`threshold` from UI
- Add `ensure_logged_in()` method
- Keep AI draft separate from template output
- Then docs would be correct

### Option C: Hybrid Approach
- Fix docs for quick wins (defaults, placeholders)
- Plan code changes for major issues (your_profile, template handling)
- Implement both together

---

## Next Steps

1. **Choose approach:** A, B, or C above
2. **Revise documents** based on chosen approach
3. **Verify corrections** with another code review pass
4. **Get AI alignment** on revised docs
5. **Then and only then** start implementing improvements

**Current Status:** BLOCKED until docs match reality

**Recommendation:** Start with Option A (document reality), then plan code changes separately
