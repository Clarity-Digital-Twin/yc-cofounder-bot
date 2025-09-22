# YC Co-Founder Bot - Current State & Fix Plan
*December 2025*

## What This Project Is
A bot that automates finding co-founders on YC's Startup School platform by:
1. **Browsing** profiles automatically using browser automation
2. **Evaluating** profiles with AI (GPT-5/GPT-4) against your criteria
3. **Messaging** high-quality matches automatically

**3 Key Inputs:**
- Your Profile (who you are)
- Match Criteria (what you're looking for)
- Message Template (how to reach out)

## What's Actually Broken

### 1. **Non-Existent OpenAI Responses API** ❌
- **Problem**: Code calls `client.responses.create()` in 8 places
- **Reality**: OpenAI SDK only has `client.chat.completions.create()`
- **Files affected**:
  - `src/yc_matcher/infrastructure/browser/openai_cua.py`
  - `src/yc_matcher/infrastructure/ai/openai_decision.py`
  - `src/yc_matcher/interface/cli/check_cua.py`

### 2. **Python Import Path Issue** ❌
- **Problem**: `ModuleNotFoundError: No module named 'yc_matcher'`
- **Cause**: Running with wrong PYTHONPATH
- **Fix**: Use `make run` or set `PYTHONPATH=src`

### 3. **Incorrect Model Names** ❌
- **Problem**: References to "gpt-5-thinking" model
- **Reality**: Model is just "gpt-5" (per OpenAI docs)

### 4. **Computer Use API Confusion** ❌
- **Problem**: Trying to use OpenAI's "Computer Use API" which isn't publicly available
- **Reality**: Need to use Playwright directly for browser automation

## How to Fix It

### Step 1: Replace Responses API with Chat Completions
```python
# WRONG (current code)
response = client.responses.create(
    model="gpt-5",
    input="...",
    ...
)

# CORRECT (should be)
response = client.chat.completions.create(
    model="gpt-5",
    messages=[{"role": "user", "content": "..."}],
    ...
)
```

### Step 2: Fix Import Paths
```bash
# Run with proper PYTHONPATH
PYTHONPATH=src streamlit run src/yc_matcher/interface/web/ui_streamlit.py

# Or use the Makefile (recommended)
make run
```

### Step 3: Remove Computer Use API References
- OpenAI doesn't have a public Computer Use API
- Use Playwright directly for browser automation
- Remove all CUA-related code or make it Playwright-only

### Step 4: Update Model Names
- Replace all "gpt-5-thinking" with "gpt-5"
- Replace all "gpt-4-thinking" with "gpt-4"

## Architecture That Would Work

```
1. Browser Automation Layer (Playwright)
   - Navigate to YC cofounder matching
   - Take screenshots
   - Extract profile text
   - Click buttons

2. Decision Layer (GPT-5/GPT-4 via Chat Completions)
   - Evaluate profiles against criteria
   - Generate match scores
   - Write personalized messages

3. Control Layer (Python/Streamlit)
   - Manage quotas and limits
   - Handle stop signals
   - Log decisions
   - Present UI
```

## What to Keep
- ✅ Clean architecture (ports/adapters)
- ✅ Safety mechanisms (quotas, deduplication)
- ✅ Streamlit UI structure
- ✅ Decision modes concept (Advisor/Rubric/Hybrid)

## What to Delete/Rewrite
- ❌ All "Responses API" code
- ❌ Computer Use API references
- ❌ Incorrect model names
- ❌ Confusing Context7 documentation

## Next Steps
1. Replace `responses.create()` with `chat.completions.create()`
2. Update all model references to correct names
3. Test with `make run` (proper PYTHONPATH)
4. Remove CUA code or make it optional/disabled by default
5. Clean up documentation to reflect reality