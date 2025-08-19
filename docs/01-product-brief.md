Product Brief

Working Name: YC Co-Founder Autonomous Matching Agent

## One-liner
A 3-input control panel (Your Profile, Match Criteria, Message Template) that deploys OpenAI's CUA to autonomously browse YC profiles, evaluate compatibility, and auto-send invites to high-scoring matches.

## Why now
- OpenAI's CUA (March 2025) available NOW via Responses API for tier 3-5 developers
- $3/1M input tokens for autonomous browser control via screenshots
- No complex scripting - CUA sees and clicks like a human
- Playwright remains as fallback only when CUA unavailable

## Goals
- **3-input simplicity**: Your Profile + Match Criteria + Message Template = Done
- **Autonomous discovery**: CUA browses profiles WITHOUT manual intervention
- **Local decision engine**: Evaluate compatibility using your exact criteria
- **Auto-messaging**: Send invites to matches above threshold (with quotas)
- **Real-time control**: STOP button, pacing, JSONL audit trail

## Non-Goals (for MVP)
- Manual profile pasting (NEVER - fully autonomous only)
- Primary Playwright usage (fallback only when CUA unavailable)
- Credential storage or CAPTCHA breaking
- Bulk spam (ethical, quota-limited outreach only)
- Multi-site support (YC-focused initially)

## Success Metrics (MVP)
- Matches contacted per day (within quota)
- Reply rate from sent invites
- Zero policy violations or unintended sends
- Cost < $0.50 per 20-profile session
- 100% autonomous (no manual profile entry)

## Stakeholders & Usage
- **Primary user**: Founders seeking cofounders on YC platform
- **Operation mode**: Set profile/criteria → Start CUA → Monitor progress
- **Frequency**: Daily/weekly sessions with 5-10 messages per run

## Technical Approach
- **Primary**: OpenAI CUA via Responses API (computer-use-preview model)
- **Fallback**: Playwright ONLY when CUA unavailable (ENABLE_PLAYWRIGHT_FALLBACK=1)
- **Decision**: Local evaluation engine with strict rubric
- **UI**: Streamlit with 3 inputs + control panel
- **Storage**: SQLite quotas/dedupe, JSONL event stream

## User Flow
1. **Configure (3 inputs)**:
   - YOUR profile (Dr. Jung's background)
   - Match criteria (what you seek)
   - Message template (personalized)

2. **Execute**:
   - Click RUN → CUA launches
   - CUA autonomously: open YC → browse → read profiles
   - Backend: evaluate each against criteria
   - If match + quota: CUA auto-sends invite

3. **Monitor**:
   - Real-time: decision events, sent confirmations
   - STOP button for emergency halt
   - Quota remaining, matches found

## Key Differentiators
- **Truly autonomous**: CUA browses WITHOUT any manual input
- **Provider flexibility**: CUA_PROVIDER=openai|anthropic|none
- **Fallback ready**: Playwright kicks in if CUA fails
- **Quota-enforced**: Hard limits prevent over-messaging
- **Audit complete**: Every decision and send logged in JSONL