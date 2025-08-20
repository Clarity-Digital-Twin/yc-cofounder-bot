# 10 — UI Reference

**Status:** Draft v0.2 (2025-08-20)  
**Owner:** UI/UX Team  
**Related:** [02-scope-and-requirements.md] · [03-architecture.md] · [05-operations-and-safety.md]

## Streamlit Dashboard - Single Page with 3 Core Inputs

### Sidebar

**Inputs (3)**
- **Your Profile** (markdown textarea)
  - Loads from CURRENT_COFOUNDER_PROFILE.MD
  - Dr. Jung's background, skills, vision, what you bring
  - Required: YES

- **Match Criteria** (markdown textarea)
  - Include must-have/should-have/disqualifiers
  - Free text or structured format
  - Required: YES

- **Message Template** (markdown textarea)
  - Supports `{first_name}`, `{why_match}`, `{my_context}`, `{their_highlight}`, `{cta}`
  - Loads from MATCH_MESSAGE_TEMPLATE.MD
  - Shows preview with sample data

**Decision**
- **Mode**: `Advisor | Rubric | Hybrid`
  - Advisor: LLM-only, requires HIL approval
  - Rubric: Deterministic scoring
  - Hybrid: Combined approach
- **Threshold**: slider 0.50–0.95 (default 0.72)
- **Alpha (Hybrid)**: slider 0.0–1.0 (default 0.50; weight on Advisor)

**Safety**
- **Shadow Mode**: checkbox (evaluate only, never send)
- **STOP**: toggle button (creates/removes `.runs/stop.flag`)
- **Pacing**: shows `PACE_MIN_SECONDS` value (read-only)
- **Quotas**: shows `DAILY_QUOTA` / `WEEKLY_QUOTA` remaining (from `.runs/quota.sqlite`)

**Provider**
- **Status**: 
  - **OpenAI Computer Use (Responses API)** — 🟢 Connected | 🔴 Unavailable
  - **Executor: Playwright** — Always used; Playwright-only fallback when `ENABLE_PLAYWRIGHT_FALLBACK=1`
- **Model**: `CUA_MODEL` (read-only), Decision LLM: `OPENAI_DECISION_MODEL` (read-only)

### Main Panel

**Run Controls**
- **Analyze**: Runs one profile (if showing a single opened profile) or starts the autonomous loop on listing pages
- **Run**: Starts the autonomous browse → read → decide → send loop (CUA primary)
- **Stop**: Same as STOP toggle; halts within ≤ 2 seconds

**Decision Results**
- Card showing:
  - **Mode**: Advisor | Rubric | Hybrid
  - **Scores**: advisor_conf, rubric_score, final_score (hybrid)
  - **Threshold**: current value
  - **Decision**: **YES** / **NO**
  - **Rationale**: ≤ 120 chars (Advisor mode or hybrid summary)
- **Approve & Send** button:
  - **Visible only when**: Mode = Advisor and Decision = YES, Shadow Mode = off
  - **Action**: Calls the currently bound **`BrowserPort`** (CUA if available; otherwise Playwright when `ENABLE_PLAYWRIGHT_FALLBACK=1`) to focus → fill → click send → verify

**Live Log**
- Tail of `events.jsonl` with filters: `decision | sent | error | quota | stop | model_usage`
- Download button for the current `events.jsonl`
- Real-time examples:
  ```
  [12:34:56] decision  | Profile: John Doe | Mode: hybrid | YES | Score: 0.76 | "Strong ML match"
  [12:34:58] sent      | Profile: John Doe | ok: true | mode: auto | 312 chars
  [12:35:02] decision  | Profile: Jane Smith | Mode: hybrid | NO | Score: 0.41 | "Different domain"
  [12:35:15] stopped   | Reason: quota_exceeded
  ```

**Counters**
- **Seen / Dedupe**: count from `.runs/seen.sqlite` (unique profiles this repo has messaged)
- **Quota**: day/week remaining; turns red at limit, blocks sending
- **Session Statistics**:
  ```
  Profiles Evaluated: 23
  Matches Found:      8 (34.8%)
  Messages Sent:      5
  Pending Approval:   3 (Advisor mode)
  Total Cost:         $0.42
  ```

### HIL Approval Queue (Advisor Mode Only)

When in Advisor mode, YES decisions appear here:
```
┌─────────────────────────────────────┐
│ John Doe - Score: HIGH              │
│ Rationale: "Strong ML background"   │
│ [View Profile] [Approve & Send]     │
└─────────────────────────────────────┘
```

## Autonomous Flow (NO MANUAL INPUT)

1. **User Configures Once**:
   - Fills 3 inputs
   - Selects decision mode
   - Sets thresholds if applicable
   - Clicks RUN

2. **CUA Takes Over**:
   - Opens YC site autonomously
   - Browses profile list
   - Clicks "View profile" for each
   - Screenshots and reads content

3. **Backend Evaluates (Per Mode)**:
   - **Advisor**: AI evaluation → queue for HIL
   - **Rubric**: Score calculation → auto-send if threshold met
   - **Hybrid**: Combined scoring → auto-send if threshold met

4. **CUA Sends (When Approved)**:
   - Fills personalized message
   - Clicks "Invite to connect"
   - Verifies send success
   - Logs sent event

5. **Loop Until**:
   - STOP pressed
   - Quota exhausted
   - No more profiles
   - Error threshold exceeded

## Environment & Launch

```env
# Engines
ENABLE_CUA=1
ENABLE_PLAYWRIGHT_FALLBACK=1      # only used if CUA fails/unavailable
ENABLE_PLAYWRIGHT=0               # force Playwright (optional, for testing)

# OpenAI
OPENAI_API_KEY=sk-...
CUA_MODEL=<your-computer-use-model>     # from your Models endpoint
CUA_TEMPERATURE=0.3
CUA_MAX_TOKENS=1200

# Decision Engine
DECISION_MODE=hybrid
OPENAI_DECISION_MODEL=<your-best-llm>
THRESHOLD=0.72
ALPHA=0.50

# Runtime
YC_MATCH_URL=https://www.startupschool.org/cofounder-matching
PACE_MIN_SECONDS=45
DAILY_QUOTA=25
WEEKLY_QUOTA=120
SHADOW_MODE=0
```

```bash
# Run (repo root; caches are repo-scoped)
uv run streamlit run -m yc_matcher.interface.web.ui_streamlit
```

## Events & Acceptance

**Event Schema (subset)**
- `decision`: `{mode, advisor_conf?, rubric_score?, final_score?, threshold, pass: bool, rationale}`
- `sent`: `{"event":"sent","ok":true,"mode":"auto","verified":true,"chars":<int>,"retry"?:1}`
- `quota`: `{day_count, week_count, allowed: bool}`
- `stop`: `{reason}`
- `error`: `{where, message, retryable: bool}`
- `model_usage`: `{provider:"openai", model, tokens_in, tokens_out, cost_est}`

**UI Acceptance Checks**
- Switching **Mode/Threshold/Alpha** immediately affects new decisions
- **Shadow Mode** prevents **Approve & Send** visibility and any send actions
- **STOP** halts within ≤ 2 seconds (no new profile opens or sends)
- When CUA is **unavailable**, the UI marks status 🔴 and automatically uses **Playwright** if `ENABLE_PLAYWRIGHT_FALLBACK=1`
- A successful send yields a `sent` event with `ok=true` and `verified=true`

## UI Copy (Canonical Labels)

- Buttons: **Analyze**, **Run**, **Stop**, **Approve & Send**
- Toggles: **Shadow Mode**, **STOP**
- Status: **OpenAI Computer Use (Responses API)**, **Executor: Playwright**
- Fields: **Your Profile**, **Match Criteria**, **Message Template**
- Modes: **Advisor**, **Rubric**, **Hybrid**

## REMOVED Features (OLD/BROKEN)

- ❌ **"Paste candidate profile" panel** - NEVER USE
- ❌ **Manual profile entry** - Fully autonomous only
- ❌ **Playwright as primary** - It's fallback only
- ❌ **Fixed scoring rules** - Now have 3 flexible modes

## Critical UI Rules

- **NO manual paste workflow** - Everything autonomous
- **Mode selector always visible** - User chooses decision approach
- **Thresholds only for Rubric/Hybrid** - Hidden in Advisor mode
- **HIL queue only in Advisor** - Other modes auto-send
- **Provider status always shown** - User knows what's running
- **Quota always visible** - Prevent surprise stops
- **Event stream always live** - Full transparency
- **Approve & Send uses current BrowserPort** - CUA first, Playwright fallback
