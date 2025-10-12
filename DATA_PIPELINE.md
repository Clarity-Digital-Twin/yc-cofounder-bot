# YC Co-Founder Matcher: Complete Data Pipeline Documentation
*Generated: 2025-10-12*

## Purpose
This document traces the **complete data flow** from user inputs → Playwright automation → OpenAI API → results. It serves as a reference for understanding, debugging, and improving the pipeline.

---

## Executive Summary

**The Playwright Pathway** (ignoring CUA):
```
User Inputs (Streamlit)
    ↓
DI Container (build_services)
    ↓
Autonomous Flow Loop
    ↓
Playwright Browser → YC Profile Pages
    ↓
OpenAI API (GPT-4/GPT-5) → Decision
    ↓
Results → Events JSONL + UI Display
```

**Key Insight**: This is NOT a deep ML/AI pipeline. It's a **workflow automation** that uses:
- Playwright for web scraping
- OpenAI API for intelligent decision-making
- SQLite for state management

---

## Phase 1: User Inputs (Streamlit UI)

### File: `/src/yc_matcher/interface/web/ui_streamlit.py`

### Inputs Collected (3 Required)
1. **Your Profile** (`str`)
   - User's background, skills, goals
   - Used by AI to evaluate match compatibility
   - Length: ~200-1000 chars typical

2. **Match Criteria** (`str`)
   - What the user is looking for in a co-founder
   - Can include technical skills, location, commitment level
   - Length: ~100-500 chars typical

3. **Message Template** (`str`)
   - Template for personalized outreach
   - Can include placeholders like `{name}`, `{skills}`
   - Length: ~50-300 chars typical

### Configuration Settings
```python
max_profiles: int = 10        # How many profiles to evaluate
auto_send: bool = True        # Auto-send if match score > threshold
shadow_mode: bool = False     # Dry-run mode (no actual sends)
threshold: float = 0.72       # Auto-send score threshold
```

### Data Validation
- ✅ All three text inputs are required (non-empty)
- ✅ Max profiles must be positive integer
- ⚠️ **NO validation** on text quality or format
- ⚠️ **NO sanitization** of template placeholders

### Output → Next Stage
```python
# Calls the autonomous flow
results = flow.run(
    your_profile=your_profile,
    criteria=criteria_text,
    template=template_text,
    mode="ai",
    limit=max_profiles,
    shadow_mode=shadow_mode,
    threshold=threshold,
    alpha=0.5
)
```

---

## Phase 2: Service Initialization (Dependency Injection)

### File: `/src/yc_matcher/interface/di.py`

### Function: `build_services()`

This wires up all the infrastructure adapters.

### Decision Adapter Setup
```python
# OpenAI client initialization
from openai import OpenAI
client = OpenAI()  # Uses OPENAI_API_KEY env var

# Create decision adapter
decision = OpenAIDecisionAdapter(
    client=client,
    logger=None,  # Attached later
    model=config.get_decision_model(),  # From OPENAI_DECISION_MODEL env
    prompt_ver="v1",
    rubric_ver="v1"
)
```

**Critical Environment Variables:**
- `OPENAI_API_KEY` - Required for API access
- `OPENAI_DECISION_MODEL` - Model name (gpt-4o, gpt-4-turbo, gpt-5, etc.)

### Browser Adapter Setup (Playwright Focus)
```python
# PLAYWRIGHT PATHWAY (ignoring CUA)
from ..infrastructure.browser.playwright_async import PlaywrightBrowserAsync

browser = PlaywrightBrowserAsync()
```

**Browser Configuration:**
- Uses async Playwright API (not sync)
- Runs through `AsyncLoopRunner` to avoid event loop conflicts
- Headless mode: `PLAYWRIGHT_HEADLESS` env var (default: visible)
- Auto-login: Uses `YC_EMAIL` and `YC_PASSWORD` if provided

### Storage & Safety Setup
```python
# Event logging
logger = LoggerWithStamps(
    JSONLLogger(Path(".runs/events.jsonl")),
    prompt_ver="v1",
    rubric_ver="v1",
    criteria_preset="custom"
)

# Quota management
quota = SQLiteDailyWeeklyQuota(Path(".runs/quota.sqlite"))

# Stop flag
stop = FileStopFlag(Path(".runs/stop.flag"))

# Deduplication
seen_repo = SQLiteSeenRepo(Path(".runs/seen.sqlite"))
```

### Output → Next Stage
Returns 3 services:
1. `EvaluateProfile` use case (wraps decision adapter + template renderer)
2. `SendMessage` use case (wraps browser + quota + logger)
3. `Logger` (for event tracking)

---

## Phase 3: Autonomous Flow Loop

### File: `/src/yc_matcher/application/autonomous_flow.py`

### Function: `run()`

This is the **main orchestrator** - loops through profiles and coordinates all steps.

### Step 1: Login Check & Navigation
```python
# Check if logged in
if not browser.is_logged_in():
    # Attempt auto-login if credentials available
    browser.ensure_logged_in()  # Uses YC_EMAIL/YC_PASSWORD

# Navigate to YC matching page
browser.open("https://www.startupschool.org/cofounder-matching")
```

**Potential Issues:**
- ⚠️ No retry logic if login fails
- ⚠️ No verification that we're on the right page
- ⚠️ Assumes YC UI structure hasn't changed

### Step 2: Profile Browsing Loop
```python
for i in range(limit):  # e.g., 10 profiles
    # Safety: Check stop flag
    if stop.is_stopped():
        break

    # Navigate to profile
    success = browser.click_view_profile()
    if not success:
        break  # No more profiles

    # Extract profile text
    profile_text = browser.read_profile_text()

    # Deduplication check
    profile_hash = hash_profile_text(profile_text)
    if seen_repo.is_seen(profile_hash):
        browser.skip()
        continue

    # Mark as seen
    seen_repo.mark_seen(profile_hash)

    # Evaluate with AI (next phase)
    evaluation = evaluate_profile(profile_text, criteria)

    # Send message if YES decision
    if evaluation["decision"] == "YES" and not shadow_mode:
        send_message(evaluation["draft"])

    # Move to next
    browser.skip()
```

### Data Transformations
1. **Profile Text Extraction** → Raw HTML text (unstructured)
2. **Hashing** → SHA256 first 16 chars for deduplication
3. **Evaluation** → Structured decision dict (see Phase 4)

### Logging Events
Every action logs a JSONL event:
```json
{"event": "profile_extracted", "profile": 0, "extracted_len": 1234, "engine": "playwright"}
{"event": "duplicate", "hash": "abc123..."}
{"event": "decision", "decision": "YES", "score": 0.85, "rationale": "..."}
{"event": "sent", "ok": true, "verified": true}
```

---

## Phase 4: Profile Evaluation (OpenAI API)

### File: `/src/yc_matcher/infrastructure/ai/openai_decision.py`

### Function: `evaluate()`

This is where the **AI magic happens** - calls OpenAI API to evaluate match quality.

### Input Preparation
```python
# Extract template from criteria if embedded
if "\nMessage Template:" in criteria.text:
    parts = criteria.text.split("\nMessage Template:")
    criteria_text = parts[0]
    template = parts[1].strip()
else:
    criteria_text = criteria.text

# Build system prompt
sys_prompt = """
You are an expert recruiter evaluating potential co-founder matches.
You MUST return a valid JSON object with these exact keys:
- decision: string 'YES' or 'NO'
- rationale: string explaining your reasoning in 1-2 sentences
- draft: if YES, a personalized message to the candidate (if NO, empty string)
- score: float between 0.0 and 1.0 indicating match strength
- confidence: float between 0.0 and 1.0 indicating your confidence
"""

# Build user prompt
user_text = f"""
MY CRITERIA:
{criteria_text}

CANDIDATE PROFILE:
{profile.raw_text}

MESSAGE TEMPLATE (use this style but personalize it):
{template}

Evaluate if this candidate matches my criteria.
If YES, write a personalized outreach message that references specific details from their profile.
"""
```

### OpenAI API Call (GPT-4 Pathway)
```python
# For GPT-4 models (gpt-4, gpt-4-turbo, gpt-4o)
response = client.chat.completions.create(
    model="gpt-4o",  # From OPENAI_DECISION_MODEL env
    messages=[
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_text}
    ],
    temperature=0.3,    # Stable for structured outputs
    max_tokens=800      # Enough for decision + message
    # NOTE: NO response_format parameter (not supported by GPT-4)
)

# Extract response
content = response.choices[0].message.content
payload = json.loads(content)  # Parse JSON
```

### OpenAI API Call (GPT-5 Pathway)
```python
# For GPT-5 models (if using gpt-5, gpt-5-mini, gpt-5-nano)
response = client.responses.create(
    model="gpt-5",
    input=[
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_text}
    ],
    max_output_tokens=800,  # Different parameter name!
    temperature=1.0,        # GPT-5 works best at 1.0
    top_p=0.9,
    truncation="auto",      # Handle long contexts
    store=True,             # Save response for retrieval
    text={"verbosity": "low"},  # Minimize reasoning output
    reasoning={"effort": "minimal"},  # Speed optimization
    response_format={       # Structured output (GPT-5 specific)
        "type": "json_schema",
        "json_schema": {
            "name": "decision_response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "decision": {"type": "string", "enum": ["YES", "NO"]},
                    "rationale": {"type": "string"},
                    "draft": {"type": "string"},
                    "score": {"type": "number", "minimum": 0, "maximum": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["decision", "rationale", "draft", "score", "confidence"],
                "additionalProperties": False
            }
        }
    }
)

# Extract response (GPT-5 returns different format)
# Uses output_text helper or manual parsing of output array
content = response.output_text  # SDK helper method
payload = json.loads(content)
```

### Response Schema (Both GPT-4 and GPT-5)
```json
{
  "decision": "YES",  // or "NO" or "ERROR"
  "rationale": "Strong ML background, local to SF",
  "draft": "Hi John, I noticed you have experience with...",
  "score": 0.85,      // 0.0-1.0 match strength
  "confidence": 0.75  // 0.0-1.0 AI confidence
}
```

### Error Handling
```python
try:
    # API call
    response = client.chat.completions.create(...)
    payload = json.loads(content)

    # Validate schema
    ok, err = _validate_decision(payload)
    if not ok:
        payload = {
            "decision": "ERROR",
            "rationale": f"Invalid model JSON: {err}",
            "draft": "",
            "score": 0.0,
            "confidence": 0.0
        }
except Exception as e:
    # Return ERROR decision (not NO)
    payload = {
        "decision": "ERROR",
        "rationale": f"OpenAI API Error: {str(e)}",
        "draft": "",
        "score": 0.0,
        "confidence": 0.0,
        "error": str(e),
        "error_type": type(e).__name__
    }
```

**Critical Distinction:**
- `"decision": "NO"` = AI evaluated and rejected (legitimate)
- `"decision": "ERROR"` = Something went wrong (API failure, invalid JSON, etc.)

### Token Usage Logging
```python
# Calculate cost estimate
inp = response.usage.input_tokens
out = response.usage.output_tokens
cost_est = (inp * 0.003 / 1000.0) + (out * 0.012 / 1000.0)

# Log usage
logger.emit({
    "event": "model_usage",
    "model": "gpt-4o",
    "tokens_in": inp,
    "tokens_out": out,
    "cost_est": cost_est
})
```

### Retry Logic
```python
# Uses RetryWithBackoff wrapper
retry = RetryWithBackoff(
    max_retries=3,
    initial_delay=2.0,
    logger=logger
)

resp, content = retry.execute(
    call_gpt4,  # or call_gpt5
    operation_name="gpt4_decision_gpt-4o",
    retryable_exceptions=(Exception,)
)
```

---

## Phase 5: Playwright Browser Automation

### File: `/src/yc_matcher/infrastructure/browser/playwright_async.py`

### Auto-Login Flow
```python
async def _auto_login_if_needed(page: Page):
    # Check if already logged in
    if await page.locator('button:has-text("View profile")').count() > 0:
        return  # Already logged in

    # Click sign in button
    sign_in = page.locator('button:has-text("Sign in")')
    await sign_in.first.click()

    # Fill email
    email_input = page.locator('input[type="email"]:visible').first
    await email_input.fill(os.getenv("YC_EMAIL"))

    # Fill password
    password_input = page.locator('input[type="password"]:visible').first
    await password_input.fill(os.getenv("YC_PASSWORD"))

    # Submit
    submit_btn = page.locator('button:has-text("Log In"):visible').first
    await submit_btn.click()

    # Wait for navigation
    await page.wait_for_url("**/cofounder-matching**", timeout=10000)
```

### Profile Navigation
```python
def click_view_profile() -> bool:
    # Check if already on profile page
    if "/candidate/" in page.url or "/profile/" in page.url:
        return True

    # Check if on dashboard
    if "dashboard" in page.url or "cofounder-matching" in page.url:
        # Click "View Profiles" button
        view_profiles = page.locator('button:has-text("View Profiles")')
        await view_profiles.first.click()
        return True

    # Try to find individual "View Profile" button
    selectors = [
        'button:has-text("View profile")',
        'button:has-text("View Profile")',
        'a:has-text("View profile")',
    ]

    for selector in selectors:
        elem = page.locator(selector).first
        if await elem.count() > 0:
            await elem.click()
            return True

    return False
```

### Profile Text Extraction
```python
def read_profile_text() -> str:
    # Strategy 1: Extract structured data
    profile_data = []

    # Get name
    name_selectors = ["h1.text-2xl", "h1", ".profile-name"]
    for sel in name_selectors:
        elem = page.locator(sel).first
        if await elem.count() > 0:
            name = await elem.inner_text()
            profile_data.append(f"Name: {name}")
            break

    # Get bio/about
    bio_selectors = [".bio", ".about", "section:has-text('About')"]
    for sel in bio_selectors:
        elem = page.locator(sel).first
        if await elem.count() > 0:
            text = await elem.inner_text()
            if len(text) > 50:
                profile_data.append(f"About: {text}")
                break

    # If structured data found, return it
    if profile_data:
        return "\n".join(profile_data)

    # Strategy 2: Fallback to main content area
    main_selectors = ["main", ".profile-content", "body"]
    for selector in main_selectors:
        elem = page.locator(selector).first
        if await elem.count() > 0:
            text = await elem.inner_text()
            if len(text) > 100:
                return text

    return ""
```

**Data Quality Issues:**
- ⚠️ No validation that extracted text is actually profile content
- ⚠️ Could extract navigation, headers, footers
- ⚠️ No structured field extraction (name, location, skills)

### Message Sending
```python
def fill_message(text: str):
    # Try multiple selector strategies
    selectors = [
        "textarea[placeholder*='excited about potentially working' i]",
        "textarea[placeholder*='type a short message' i]",
        "textarea",
        "[contenteditable='true']",
        "div[role='textbox']",
    ]

    for selector in selectors:
        elem = page.locator(selector).first
        if await elem.count() > 0 and await elem.is_visible():
            await elem.click()

            # Handle contenteditable differently
            if "contenteditable" in selector:
                await page.keyboard.press("Control+a")
                await page.keyboard.type(text)
            else:
                await elem.fill(text)
            return

def send():
    # Try to find send button
    selectors = [
        "button:has-text('Invite to connect')",
        "button.bg-green-500",
        "button:has-text('Send')",
    ]

    for selector in selectors:
        elem = page.locator(selector).first
        if await elem.count() > 0 and await elem.is_visible():
            await elem.click()
            return

def verify_sent() -> bool:
    # Look for success indicators
    page_text = await page.locator("body").inner_text()
    success_patterns = ["Message sent", "Successfully sent", "✓"]

    for pattern in success_patterns:
        if pattern.lower() in page_text.lower():
            return True

    return False
```

---

## Phase 6: Results Processing & Display

### Event Logging
All events are appended to `.runs/events.jsonl` in real-time.

**Event Types:**
1. `autonomous_start` - Flow begins
2. `profile_extracted` - Profile text scraped
3. `duplicate` - Profile already seen
4. `decision` - AI evaluation complete
5. `model_usage` - Token/cost tracking
6. `sent` - Message sent successfully
7. `evaluation_error` - AI evaluation failed
8. `autonomous_complete` - Flow finished

### Results Summary
```python
{
    "total_evaluated": 10,
    "total_sent": 3,
    "total_skipped": 2,
    "mode": "ai",
    "shadow": false,
    "results": [
        {
            "profile_num": 0,
            "hash": "abc123...",
            "decision": "YES",
            "rationale": "Strong ML background, local to SF",
            "sent": true,
            "mode": "ai"
        },
        {
            "profile_num": 1,
            "hash": "def456...",
            "decision": "NO",
            "rationale": "Looking for non-technical co-founder",
            "sent": false,
            "mode": "ai"
        },
        ...
    ]
}
```

### UI Display
Streamlit shows:
- **Status Bar**: Evaluated / Sent / Skipped / Remaining quota
- **Results Table**: Profile # | Decision | Rationale | Sent
- **Events Panel**: Last 10 events from JSONL

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUTS                              │
│  (Streamlit UI: Profile, Criteria, Template, Config)            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DEPENDENCY INJECTION                           │
│  • OpenAI Client (API key)                                       │
│  • Playwright Browser (async)                                    │
│  • Logger (JSONL)                                                │
│  • Quota (SQLite)                                                │
│  • Seen Repo (SQLite)                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS FLOW LOOP                          │
│  FOR each profile (up to limit):                                 │
│    1. Check stop flag                                            │
│    2. Navigate to profile ──────────────┐                        │
│    3. Extract text                      │                        │
│    4. Check if seen                     │                        │
│    5. Evaluate with AI ──────────┐      │                        │
│    6. Send if YES                │      │                        │
│    7. Log events                 │      │                        │
└──────────────────────────────────┼──────┼────────────────────────┘
                                   │      │
                   ┌───────────────┘      └───────────────┐
                   ▼                                      ▼
┌────────────────────────────────────┐  ┌─────────────────────────┐
│     OPENAI API EVALUATION          │  │  PLAYWRIGHT AUTOMATION  │
│                                    │  │                         │
│  INPUT:                            │  │  ACTIONS:               │
│  • Profile text (1000 chars)      │  │  • Login (auto)         │
│  • Criteria (500 chars)           │  │  • Navigate             │
│  • Template (200 chars)           │  │  • Click buttons        │
│                                    │  │  • Extract text         │
│  API CALL:                         │  │  • Fill message box     │
│  • Model: gpt-4o / gpt-5          │  │  • Click send           │
│  • Temperature: 0.3 / 1.0         │  │  • Verify sent          │
│  • Max tokens: 800                 │  │                         │
│  • Retry: 3x with backoff         │  │  DATA OUT:              │
│                                    │  │  • Profile text (str)   │
│  OUTPUT:                           │  │  • Success (bool)       │
│  {                                 │  │                         │
│    "decision": "YES/NO/ERROR",    │  └─────────────────────────┘
│    "rationale": "...",             │
│    "draft": "...",                 │
│    "score": 0.85,                  │
│    "confidence": 0.75              │
│  }                                 │
│                                    │
│  USAGE:                            │
│  • Input tokens: ~1200             │
│  • Output tokens: ~150             │
│  • Cost: ~$0.005 per profile      │
└────────────┬───────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       RESULTS & LOGGING                          │
│                                                                   │
│  STORAGE:                                                         │
│  • .runs/events.jsonl  - Event stream (append-only)             │
│  • .runs/seen.sqlite   - Profile hashes (dedup)                 │
│  • .runs/quota.sqlite  - Daily/weekly send counts               │
│                                                                   │
│  UI DISPLAY:                                                      │
│  • Status bar (evaluated/sent/remaining)                         │
│  • Results table (decisions + rationales)                        │
│  • Events panel (last 10 events)                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Critical Data Validation Gaps

### Input Validation (Phase 1)
- ❌ No validation of criteria quality
- ❌ No sanitization of template placeholders
- ❌ No length limits on text inputs
- ❌ No check that template is actually a template

### Profile Extraction (Phase 5)
- ❌ No validation that extracted text is a profile
- ❌ Could extract navigation, ads, error messages
- ❌ No structured field extraction
- ❌ No minimum content length check

### OpenAI Response (Phase 4)
- ✅ JSON schema validation (good!)
- ✅ Retry logic with backoff (good!)
- ⚠️ But falls back to ERROR decision (loses data)
- ❌ No check if rationale makes sense
- ❌ No verification that draft references profile

### Message Sending (Phase 5)
- ❌ No verification that message was actually sent
- ❌ `verify_sent()` only checks for success text
- ❌ Could send duplicate messages if verification fails
- ❌ No screenshot or DOM state capture

### Event Logging (Phase 6)
- ✅ All events logged with timestamps (good!)
- ⚠️ But events can be incomplete (missing fields)
- ❌ No event replay mechanism
- ❌ No way to resume from failure

---

## Token Usage & Cost Tracking

### Per-Profile Cost Estimate
```
Input tokens:  ~1200  (profile + criteria + system prompt)
Output tokens: ~150   (decision JSON + message draft)

Cost (GPT-4o):
  Input:  1200 * $0.003 / 1000 = $0.0036
  Output:  150 * $0.012 / 1000 = $0.0018
  Total:  ~$0.0054 per profile

Cost (GPT-4-turbo):
  Input:  1200 * $0.001 / 1000 = $0.0012
  Output:  150 * $0.004 / 1000 = $0.0006
  Total:  ~$0.0018 per profile

Cost (GPT-5):
  Input:  1200 * $0.015 / 1000 = $0.018
  Output:  150 * $0.06 / 1000  = $0.009
  Total:  ~$0.027 per profile
```

### Session Cost
```
10 profiles:   $0.05 - $0.27
50 profiles:   $0.25 - $1.35
100 profiles:  $0.50 - $2.70
```

### Logging
Token usage is logged for every API call:
```json
{
  "event": "model_usage",
  "model": "gpt-4o",
  "tokens_in": 1234,
  "tokens_out": 156,
  "cost_est": 0.0054
}
```

---

## API Configuration Reference

### Environment Variables (Required)
```bash
# OpenAI Authentication
OPENAI_API_KEY=sk-...

# Model Selection
OPENAI_DECISION_MODEL=gpt-4o  # or gpt-4-turbo, gpt-5, etc.

# YC Credentials (for auto-login)
YC_EMAIL=your-email@example.com
YC_PASSWORD=your-password
```

### Environment Variables (Optional)
```bash
# Browser Configuration
PLAYWRIGHT_HEADLESS=0           # 1 = headless, 0 = visible
PLAYWRIGHT_BROWSERS_PATH=/path  # Custom browser install path

# GPT-5 Specific (if using gpt-5 models)
GPT5_MAX_TOKENS=800             # Max output tokens
GPT5_TEMPERATURE=1.0            # 1.0 recommended for GPT-5
GPT5_TOP_P=0.9                  # Nucleus sampling
GPT5_VERBOSITY=low              # low/medium/high
GPT5_REASONING_EFFORT=minimal   # minimal/low/medium/high

# Safety & Limits
DAILY_QUOTA=25                  # Max sends per day
WEEKLY_QUOTA=120                # Max sends per week
SHADOW_MODE=0                   # 1 = test only, no sends
THRESHOLD=0.72                  # Auto-send threshold
```

### API Endpoints Used
```
OpenAI Chat Completions API (GPT-4):
  POST https://api.openai.com/v1/chat/completions

OpenAI Responses API (GPT-5):
  POST https://api.openai.com/v1/responses

YC Cofounder Matching:
  https://www.startupschool.org/cofounder-matching
```

---

## Next Steps

This document serves as the **baseline** for understanding the current pipeline. The next phase is to:

1. **Identify specific bugs and gaps** (documented in separate file)
2. **Create validation tests** for each phase
3. **Implement data quality checks**
4. **Add monitoring and observability**
5. **Improve error recovery**

See companion document: `PIPELINE_ISSUES.md` (to be created)
