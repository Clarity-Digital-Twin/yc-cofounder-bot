# ACTION PLAN - MAKING THIS SHIT WORK

## IMMEDIATE FIXES (to get it working NOW)

### 1. Fix the "already on profile" bug
**Problem**: After login, YC goes directly to `/candidate/XYZ`, no "View Profile" button
**Fix**: In `browser_playwright_async.py`:
```python
def click_view_profile(self):
    if "/candidate/" in page.url:
        return True  # Already viewing a profile!
    # ... rest of existing code
```

### 2. Fix CUA model name
**In .env**:
```env
CUA_MODEL=computer-use-preview  # NOT gpt-4-vision-preview
ENABLE_CUA=1  # Turn it on to test
```

### 3. Fix Decision Flow
The flow should be:
1. Extract profile text
2. **Hybrid Mode**: 
   - First: Rubric scores keywords (Python=3, FastAPI=2, etc.)
   - If score >= 0.72 threshold → 
   - Then: Ask GPT-4 "Should I match with this person?"
   - GPT-4 returns: {decision: "YES", rationale: "...", draft: "Hey [name]..."}
3. If YES → Send message (unless SHADOW_MODE=1)

## HOW TO TEST RIGHT NOW

### Test 1: Playwright-only (currently working)
```bash
ENABLE_CUA=0 ENABLE_PLAYWRIGHT=1 python test_everything_works.py
```

### Test 2: With CUA enabled
```bash
ENABLE_CUA=1 CUA_MODEL=computer-use-preview python test_everything_works.py
```

### Test 3: Test decision evaluation
```python
# Create a test profile
profile = Profile(raw_text="I'm a Python developer with FastAPI experience...")
criteria = Criteria(text="Python, FastAPI, Healthcare")

# Test evaluation
result = eval_use(profile, criteria)
print(result)  # Should show decision, rationale, draft
```

## THE BIG PICTURE

### What we have:
1. ✅ **Playwright browser control** - works, auto-login works
2. ✅ **OpenAI CUA implementation** - complete but untested
3. ✅ **Decision modes** - all three implemented
4. ⚠️ **Profile detection** - buggy (easy fix)
5. ⚠️ **CUA not enabled** - just needs env var

### How it SHOULD work:

**Option A: Playwright-only (fast, reliable)**
- Playwright does everything with selectors
- Good for stable sites like YC

**Option B: CUA + Playwright (smart, adaptive)**
- CUA looks at screenshot: "I see a profile, click View"
- Playwright executes the click
- CUA: "Now I see profile details, extract the text"
- Playwright extracts
- Loop continues

### Decision flow (your ChatGPT mirror):
```
Profile Text → Rubric Score → Above threshold? 
    ↓ YES
Ask GPT-4 → "Match with this person?"
    ↓ YES
Generate message → Send (if not shadow mode)
```

## WHAT TO DO NOW

### Step 1: Fix the immediate bugs
1. Fix `/candidate/` detection
2. Update CUA_MODEL in .env
3. Test with `python test_everything_works.py`

### Step 2: Verify decision flow
1. Add logging to see decisions
2. Confirm GPT-4 is being called
3. Check message generation

### Step 3: Choose your mode
- **For testing**: Use SHADOW_MODE=1 (won't actually send)
- **For production**: SHADOW_MODE=0 + choose engine:
  - Stable YC site → Playwright-only (ENABLE_CUA=0)
  - Dynamic/new sites → CUA enabled (ENABLE_CUA=1)

## THE TRUTH

We built everything but:
1. Small bug preventing profile detection
2. Wrong model name for CUA
3. Haven't tested the full loop

Fix these 2 things and it should work!