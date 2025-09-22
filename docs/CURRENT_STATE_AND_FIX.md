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

## Current Implementation Status

### What's Actually Implemented ✅
1. **Playwright Browser Automation** - WORKING
   - Auto-login to YC implemented
   - Profile navigation with `/candidate/` detection fixed
   - Screenshot capture and text extraction

2. **Decision Modes** - ALL THREE IMPLEMENTED
   - **Advisor**: GPT-based evaluation with manual approval
   - **Rubric**: Deterministic keyword scoring
   - **Hybrid**: Combines both approaches

3. **Safety Mechanisms** - WORKING
   - STOP flag handling
   - Daily/weekly quotas
   - Deduplication (won't message same person twice)
   - Shadow mode for testing

### What's Actually Broken

### 1. **Non-Existent OpenAI Responses API** ❌
- **Problem**: Code calls `client.responses.create()` in 8 places
- **Reality**: OpenAI SDK v1.64.0 doesn't have a `responses` attribute
- **Historical Context**: Project tried to implement "Computer Use API" that doesn't exist in OpenAI
- **Files affected**:
  - `src/yc_matcher/infrastructure/browser/openai_cua.py`
  - `src/yc_matcher/infrastructure/ai/openai_decision.py`
  - `src/yc_matcher/interface/cli/check_cua.py`

### 2. **Python Import Path Issue** ❌
- **Problem**: `ModuleNotFoundError: No module named 'yc_matcher'`
- **Cause**: Running without proper PYTHONPATH
- **Fix**: Use `make run` or set `PYTHONPATH=src`

### 3. **Configuration Issues**
- **CUA disabled**: `ENABLE_CUA=0` (correctly disabled since it doesn't exist)
- **Using Playwright**: `ENABLE_PLAYWRIGHT=1` (this is the working path)
- **Model confusion**: References to "gpt-5" which may not be available

## The Real Situation (Based on Historical Docs)

According to the historical fixes documentation:
1. **The project DID try to implement OpenAI's "Responses API"** for GPT-5
2. **They believed this API existed** and tried to make it work with fallbacks
3. **The `/candidate/` bug was already fixed** in the Playwright implementation
4. **Decision modes are implemented** but use the non-existent Responses API

### What the Docs Claim vs Reality
- **Docs claim**: "Responses API with GPT-5 working"
- **Reality**: OpenAI SDK doesn't have `client.responses`
- **Docs claim**: "Computer Use API via Responses API"
- **Reality**: Neither exists in public OpenAI

## Two Possible Paths Forward

### Option 1: Strip Out Non-Existent APIs (Recommended)
```python
# Replace all client.responses.create() with:
response = client.chat.completions.create(
    model="gpt-4",  # or gpt-3.5-turbo
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3
)
```

### Option 2: Wait for Clarity on "Computer Use"
- Keep the CUA code but disabled (`ENABLE_CUA=0`)
- Use Playwright-only mode for now
- Research if there's a beta API we're missing

## What DOES Work Right Now

1. **Playwright Browser Control** ✅
   - Login to YC
   - Navigate profiles
   - Extract text
   - Click buttons

2. **The Architecture** ✅
   - Clean ports/adapters design
   - Safety mechanisms
   - UI structure

3. **What to Run** ✅
   ```bash
   # This should work with Playwright-only mode:
   PYTHONPATH=src make run
   ```

## Immediate Action Items
1. **Test with Playwright-only mode** (CUA disabled)
2. **Replace responses.create() with chat.completions.create()**
3. **Use gpt-4 or gpt-3.5-turbo** (known working models)
4. **Document what actually works vs aspirational features**