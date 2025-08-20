UI Reference

## Streamlit Dashboard - Single Page with 3 Core Inputs

### Section 1: Core Inputs

#### INPUT 1: Your Profile
- **What**: Dr. Jung's background, skills, vision, what you bring
- **Source**: Loads from CURRENT_COFOUNDER_PROFILE.MD
- **Format**: Multi-line text area (markdown supported)
- **Required**: YES - this defines who YOU are

#### INPUT 2: Match Criteria
- **Format Options**:
  - **Free Text Mode**: "Looking for a technical cofounder with ML experience..."
  - **Structured Mode** (Advanced):
    - Technical skills checkboxes
    - Domain/industry selectors
    - Location requirements
    - Commitment level (full-time, part-time)
    - Stage preference (idea, MVP, revenue)
- **Required**: YES - defines your ideal match

#### INPUT 3: Message Template
- **What**: Your personalized outreach message
- **Source**: Loads from MATCH_MESSAGE_TEMPLATE.MD
- **Variables Available**:
  - `{name}` - Candidate's name
  - `{tech}` - Matching technical skills
  - `{hook}` - Personalized connection point
  - `{city}` - Their location
  - `{why_match}` - Reason for reaching out
- **Preview**: Shows rendered example with sample data

### Section 2: Decision Controls

#### Mode Selector (Radio Buttons)
- **Advisor Mode** 🤔
  - Pure AI evaluation ("Is this a good fit?")
  - No auto-send, requires manual approval
  - Best for: Cautious exploration

- **Rubric Mode** 📊
  - Deterministic scoring based on criteria
  - Auto-sends if score > threshold
  - Best for: Clear, quantifiable requirements

- **Hybrid Mode** 🔄
  - Combines AI judgment with rubric scoring
  - Weighted blend (configurable alpha)
  - Best for: Balanced approach

#### Mode-Specific Controls

**For Rubric & Hybrid Modes:**
- **Threshold Slider**: 0.0 to 1.0 (default 0.72)
  - Label: "Auto-send if score ≥ [value]"

**For Hybrid Mode Only:**
- **Alpha Slider**: 0.0 to 1.0 (default 0.30)
  - Label: "AI weight: [α]% AI, [1-α]% Rubric"

**For All Modes:**
- **Strict Rules Toggle**: ☑️ "Hard rules must pass"
  - When enabled, certain criteria are mandatory

### Section 3: Execution Controls

#### Main Controls
- **RUN Button** ▶️: Start autonomous session
- **STOP Button** ⏹️: Immediate halt (sets stop flag)
- **Shadow Mode Toggle** 👻: "Evaluate only (no sends)"

#### Provider Selection
- **Status**: OpenAI Computer Use (via Agents SDK)
  - Playwright Fallback (auto-activates if CUA fails)
- **Status Indicator**: 🟢 Connected | 🔴 Unavailable

#### Quota Display
```
Daily:   [████████░░] 16/20 remaining
Weekly:  [██████░░░░] 42/60 remaining
```

### Section 4: Live Monitoring

#### Event Stream Panel
Real-time tail of JSONL events:
```
[12:34:56] decision  | Profile: John Doe | Mode: hybrid | YES | Score: 0.76 | "Strong ML match"
[12:34:58] sent      | Profile: John Doe | ok: true | mode: auto | 312 chars
[12:35:02] decision  | Profile: Jane Smith | Mode: hybrid | NO | Score: 0.41 | "Different domain"
[12:35:15] stopped   | Reason: quota_exceeded
```

#### Session Statistics
```
Profiles Evaluated: 23
Matches Found:      8 (34.8%)
Messages Sent:      5
Pending Approval:   3 (Advisor mode)
Total Cost:         $0.42
```

### Section 5: HIL Approval Queue (Advisor Mode Only)

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

## Environment Variables

```bash
# Core Configuration
ENABLE_CUA=1
# OpenAI Computer Use via Agents SDK
OPENAI_API_KEY=sk-...

# Decision Configuration
DECISION_MODE=advisor  # or rubric or hybrid
THRESHOLD=0.72         # for rubric/hybrid
ALPHA=0.30            # for hybrid only
STRICT_RULES=1        # enforce hard requirements

# Fallback
ENABLE_PLAYWRIGHT_FALLBACK=1

# Quotas and Pacing
DAILY_LIMIT=20
WEEKLY_LIMIT=60
SEND_DELAY_MS=5000

# Target
YC_MATCH_URL=https://www.startupschool.org/cofounder-matching
```

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