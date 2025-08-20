Product Brief

Working Name: YC Co-Founder Autonomous Matching Agent

## One-liner
A 3-input control panel (Your Profile, Match Criteria, Message Template) that deploys CUA to autonomously browse YC profiles, evaluates via configurable decision modes (Advisor/Rubric/Hybrid), and auto-sends invites with quota safeguards.

## Why now
- OpenAI Computer Use (2025) available NOW via Agents SDK
- $3/1M input tokens for autonomous browser control via Computer Use tool
- No complex scripting - CUA model sees and clicks like a human
- Flexible decision modes: from pure AI judgment to deterministic scoring

## Goals
- **3-input simplicity**: Your Profile + Match Criteria + Message Template = Done
- **Autonomous discovery**: CUA browses profiles WITHOUT manual intervention
- **Flexible decisions**: Three modes - Advisor (AI-only), Rubric (rules), Hybrid (both)
- **Guarded auto-send**: Messages sent only with approval (mode-dependent) and within quotas
- **Real-time control**: STOP button, pacing, JSONL audit trail

## Decision Modes
1. **Advisor Mode** (LLM-only, no auto-send)
   - AI evaluates like ChatGPT: "Is this a good fit?"
   - Returns YES/NO + rationale
   - Requires manual approval to send (HIL)

2. **Rubric Gate Mode** (deterministic, auto-send)
   - Structured scoring against criteria
   - Threshold-based decisions
   - Auto-sends if score > threshold + quota available

3. **Hybrid Mode** (guardrails + AI, auto-send)
   - Combines rubric score with LLM confidence
   - Hard rules must pass first
   - Auto-sends if final_score > threshold + quota available

## Non-Goals (for MVP)
- Manual profile pasting (NEVER - fully autonomous only)
- Primary Playwright usage (fallback only when CUA unavailable)
- Credential storage or CAPTCHA breaking
- Bulk spam (ethical, quota-limited outreach only)
- Multi-site support (YC-focused initially)

## Success Metrics (MVP)
- Matches contacted per day (within quota)
- Reply rate from sent invites
- Decision accuracy (validated against manual review)
- Zero policy violations or unintended sends
- Cost < $0.50 per 20-profile session

## Technical Approach
- **Primary**: OpenAI Computer Use via Agents SDK
- **Fallback**: Playwright ONLY when CUA unavailable (ENABLE_PLAYWRIGHT_FALLBACK=1)
- **Decision Engine**: Mode-configurable (Advisor/Rubric/Hybrid)
- **UI**: Streamlit with 3 inputs + mode selector + control panel
- **Storage**: SQLite quotas/dedupe, JSONL event stream

## User Flow
1. **Configure (3 inputs + mode)**:
   - YOUR profile (Dr. Jung's background)
   - Match criteria (structured or free text)
   - Message template (with variables)
   - Select decision mode (Advisor/Rubric/Hybrid)

2. **Execute**:
   - Click RUN → CUA launches
   - CUA autonomously: open YC → browse → read profiles
   - Backend: evaluate per selected mode
   - If approved + quota: CUA auto-sends invite (Rubric/Hybrid) or waits for HIL (Advisor)

3. **Monitor**:
   - Real-time: decision events with scores/rationale
   - Sent confirmations with verification
   - STOP button for emergency halt
   - Quota remaining display

## Safety Features
- **STOP flag**: Immediate halt capability
- **Quotas**: Daily/weekly hard limits
- **Pacing**: Configurable delay between sends
- **Deduplication**: Never message same profile twice
- **Shadow Mode**: Evaluate-only without sending
- **HIL option**: Manual approval in Advisor mode

## Key Differentiators
- **Three decision modes**: Flexible from pure AI to pure rules
- **Truly autonomous**: CUA browses WITHOUT any manual input
- **OpenAI Computer Use**: Direct integration via Agents SDK
- **Fallback ready**: Playwright kicks in if CUA fails
- **Audit complete**: Every decision and send logged with versioning