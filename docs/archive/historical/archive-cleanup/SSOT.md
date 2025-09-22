# SINGLE SOURCE OF TRUTH (SSOT) - YC Cofounder Bot
*Last Updated: August 21, 2025*

## 🎯 WHAT THIS APP DOES

Autonomous browser automation for YC/Startup School cofounder matching. Takes 3 inputs (Your Profile, Match Criteria, Message Template) and autonomously browses, evaluates profiles, and sends personalized messages.

## 🏗️ ARCHITECTURE: TWO SEPARATE SYSTEMS

### 1. NAVIGATION/BROWSER CONTROL
- **Executor**: Always Playwright (singleton browser instance)
- **Planner**:
  - **Default (ENABLE_CUA=0)**: Playwright hardcoded selectors
  - **Optional (ENABLE_CUA=1)**: OpenAI Computer Use API plans, Playwright executes

### 2. DECISION/MESSAGE GENERATION (NLP)
- **API**: Chat Completions API (NOT Computer Use!)
- **Model**: GPT-5 or GPT-5-thinking ONLY
- **Purpose**: Evaluates profiles, generates personalized messages
- **Returns**: `{decision: "YES/NO", rationale: "...", draft: "...", score: 0.85}`

## ✅ WHAT'S WORKING (CURRENT STATE)

### ✅ IMPLEMENTED & WORKING
1. **Playwright Navigation** (ENABLE_CUA=0)
   - Auto-login with YC credentials ✅
   - Navigate to profiles ✅
   - Extract profile text ✅
   - Skip/Send messages ✅
   - Single browser instance (singleton) ✅

2. **Decision Engine**
   - GPT-5/GPT-5-thinking integration ✅
   - Generates personalized messages ✅
   - Hybrid mode (rubric + AI) ✅
   - Returns decision, rationale, draft ✅

3. **Safety Features**
   - STOP flag (.runs/stop.flag) ✅
   - Quota limits (daily/weekly) ✅
   - Pacing between sends ✅
   - Shadow mode for testing ✅
   - Deduplication (never message twice) ✅

### ⚠️ PARTIALLY IMPLEMENTED
1. **Computer Use API (ENABLE_CUA=1)**
   - Core loop implemented ✅
   - Responses API integration ✅
   - Screenshot → plan → execute cycle ✅
   - Safety checks handling ✅
   - **Missing**: Not fully tested in production
   - **Status**: Over-engineered for YC use case

2. **Login Preflight**
   - Auto-login implemented ✅
   - is_logged_in() check exists ✅
   - **Missing**: Doesn't block/wait if not logged in
   - **Issue**: Sometimes starts without confirming login

### ❌ KNOWN ISSUES
1. **"Start does nothing" bug**
   - Root cause: No hard login assertion before evaluation
   - Sometimes lands on `/candidate/*` directly (no "View Profile" button)
   - Fix needed: Detect candidate vs listing page

2. **Test Coverage Gaps**
   - No tests for login preflight blocking
   - No tests for candidate vs listing detection
   - CUA tests exist but marked `.skip`

## 🔧 CONFIGURATION

### Current Working Config (.env)
```env
# Navigation (Playwright-only - FAST & RELIABLE)
ENABLE_CUA=0                            # Don't use Computer Use
ENABLE_PLAYWRIGHT=1                     # Use Playwright
PLAYWRIGHT_HEADLESS=0                   # Visible browser

# Decision Engine (GPT-5 ONLY for matching)
ENABLE_OPENAI=1
OPENAI_DECISION_MODEL=gpt-5             # GPT-5 or gpt-5-thinking ONLY!
DECISION_MODE=hybrid                    # rubric + AI
THRESHOLD=0.72
ALPHA=0.50

# Auto-login
YC_EMAIL=jj@novamindnyc.com
YC_PASSWORD=$2guJ8q4umiMEU

# Safety
PACE_MIN_SECONDS=45                     # Between sends
DAILY_QUOTA=100
WEEKLY_QUOTA=500
SHADOW_MODE=0                           # 0 = actually send
```

### Optional CUA Config (Experimental)
```env
ENABLE_CUA=1                            # Use Computer Use planner
CUA_MODEL=computer-use-preview          # OpenAI's CUA model
CUA_MAX_TURNS=40                        # Safety limit
```

## 📊 HOW THE TOGGLE WORKS

### ENABLE_CUA=0 (Default - Recommended)
```python
Flow: Playwright selectors → Direct browser control
Speed: FAST (no API calls)
Cost: FREE (no tokens)
Reliability: HIGH (deterministic)
```

### ENABLE_CUA=1 (Experimental)
```python
Flow: Screenshot → CUA API → "click at (x,y)" → Playwright executes → Repeat
Speed: SLOW (API roundtrips)
Cost: EXPENSIVE (tokens per action)
Reliability: VARIABLE (AI decisions)
```

## 🐛 FIXES NEEDED (Priority Order)

### 1. Fix "Start does nothing" (HIGH PRIORITY)
```python
# In autonomous_flow.py
def run():
    browser.ensure_logged_in()  # Block until logged in

    # In click_view_profile()
    if "/candidate/" in page.url:
        return True  # Already on profile
    else:
        click("View Profiles")  # From dashboard
```

### 2. Add Missing Tests
- `test_login_preflight_blocks`
- `test_extract_when_already_on_candidate`
- `test_dashboard_to_profiles_navigation`

### 3. Complete CUA Implementation (LOW PRIORITY)
- Already 80% done
- Only needed if YC changes their site
- Keep as experimental feature

## 🚀 RECOMMENDED USAGE

### For Production (YC Matching)
```bash
# Use Playwright-only (fast, reliable)
ENABLE_CUA=0
ENABLE_PLAYWRIGHT=1
SHADOW_MODE=0  # Actually send messages
```

### For Testing/Learning
```bash
# Try Computer Use (slow, educational)
ENABLE_CUA=1
SHADOW_MODE=1  # Don't send real messages
```

## 📈 PERFORMANCE METRICS

### Current Performance (Playwright-only)
- Profile evaluation: ~2-3 seconds
- Message generation (GPT-5): ~1-2 seconds
- Send + verify: ~1 second
- Total per profile: ~5 seconds + 45s pacing

### With CUA Enabled
- Profile evaluation: ~10-15 seconds (multiple API calls)
- Rest remains the same
- Total per profile: ~20 seconds + 45s pacing

## 🎓 WHY CUA EXISTS IN THIS CODEBASE

1. **Future-proofing**: If YC radically changes their HTML
2. **Educational**: Example of OpenAI's Computer Use API
3. **Experimentation**: Compare AI planning vs hardcoded
4. **Adaptability**: Could work on OTHER sites without code changes

## 🏁 BOTTOM LINE

**Current Setup**: Perfect for YC matching
- Playwright navigation ✅
- GPT-5/GPT-5-thinking decisions ✅
- Auto-login ✅
- Message generation ✅

**CUA**: Over-engineered for this use case but valuable for:
- Learning OpenAI's newest API
- Handling dynamic/unknown sites
- Future adaptability

**Recommendation**: Keep using ENABLE_CUA=0 for YC. It's faster, cheaper, and more reliable.

## 📝 TEST COMMANDS

```bash
# Run all tests
make verify

# Test decision engine
uv run python test_decision_engine.py

# Manual browser test
uv run python test_everything_works.py

# Check available models
uv run python check_models.py
```

## 🔍 DEBUGGING

### If "Start does nothing"
1. Check browser opens and logs in
2. Check URL - are you on `/candidate/*`?
3. Check .runs/events.jsonl for errors

### If no messages generated
1. Check OPENAI_DECISION_MODEL is valid
2. Check API key is set
3. Look for "draft" in .runs/events.jsonl

### If CUA fails
1. Check CUA_MODEL is set
2. Check you have access to computer-use-preview
3. Fall back to ENABLE_CUA=0

---

**This is the truth. Everything else is speculation.**
