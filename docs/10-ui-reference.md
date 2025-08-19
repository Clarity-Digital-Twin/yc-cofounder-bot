UI Reference

## Streamlit Dashboard - 3 Core Inputs

### INPUT 1: Your Profile
- **What**: Dr. Jung's background, skills, vision
- **Source**: Loads from CURRENT_COFOUNDER_PROFILE.MD
- **Format**: Multi-line text area
- **Required**: YES - this is YOUR identity

### INPUT 2: Match Criteria
- **What**: Exactly what you're looking for
- **Controls**:
  - Technical skills checkboxes
  - Domain/industry selectors
  - Location requirements
  - Commitment level (full-time, part-time)
- **Threshold**: Score slider (default 80% for auto-send)

### INPUT 3: Message Template
- **What**: Your outreach message
- **Source**: Loads from MATCH_MESSAGE_TEMPLATE.MD
- **Variables**: {name}, {tech_match}, {shared_interest}
- **Preview**: Shows with sample substitutions

### Control Panel
- **RUN Button**: Start autonomous session
- **STOP Button**: Immediate halt (sets stop flag)
- **Provider Selector**: 
  - OpenAI CUA (primary)
  - Anthropic CUA (alternative)
  - Playwright (fallback only)
- **Mode Toggle**:
  - Live (sends messages)
  - Shadow (evaluate only, no sends)
- **Quota Display**: 
  - Daily: X/20 remaining
  - Weekly: Y/60 remaining

### Live Event Stream (JSONL)
- **decision**: {profile_id, score, YES/NO, rationale}
- **sent**: {profile_id, ok:true, mode:auto}
- **stopped**: {reason: user_requested|quota_exceeded}
- **model_usage**: {provider, tokens, cost}
- **Format**: Real-time tail of events.jsonl

### Session Summary
- **Metrics**:
  - Profiles evaluated: N
  - Matches found: M (score > threshold)
  - Messages sent: S
  - Success rate: S/M
  - Total cost: $X.XX
- **NO MANUAL PASTE**: Never show "paste profile" UI

## YC Site Elements (for CUA)

### Login Page
- **URL**: From WEBSITE_LINK.MD
- **Elements**: Email/password fields, login button
- **Screenshot**: initial_log_in.png

### Profile List Page
- **Elements**:
  - Profile cards with summary
  - "View profile" buttons
  - Pagination/infinite scroll
- **CUA Actions**: Scroll, click profiles

### Individual Profile Page
- **Screenshot**: view_profile_clicked.png
- **Main Content**:
  - About section
  - Background/experience
  - Skills and interests
  - What they're looking for
- **Message Panel**:
  - Text area for message
  - "Invite to connect" button
  - Character limit indicator

## Autonomous Flow (NO MANUAL INPUT)

1. **User Configures Once**:
   - Enters 3 inputs
   - Clicks RUN

2. **CUA Takes Over**:
   - Opens YC autonomously
   - Browses profile list
   - Clicks "View profile" for each
   - Screenshots and reads content

3. **Backend Evaluates**:
   - Local decision engine scores profile
   - Compares to threshold
   - Logs decision event

4. **CUA Sends (if match)**:
   - Fills personalized message
   - Clicks "Invite to connect"
   - Verifies send success
   - Logs sent event

5. **Loop Until**:
   - STOP pressed
   - Quota exhausted
   - No more profiles

## Key Environment Variables
```bash
# Primary Configuration
ENABLE_CUA=1
CUA_PROVIDER=openai  # or anthropic
CUA_API_KEY=sk-...

# Fallback Option
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

## Critical Reminders
- **CUA is PRIMARY**: OpenAI/Anthropic CUA does the work
- **Playwright is FALLBACK**: Only when CUA unavailable
- **3 inputs only**: Profile, Criteria, Template
- **Fully autonomous**: No manual intervention
- **Event-driven**: Everything logged to JSONL