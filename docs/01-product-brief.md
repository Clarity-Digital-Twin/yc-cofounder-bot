Product Brief

Working Name: YC Co-Founder Autonomous Matching Agent

## One-liner
An autonomous matching agent that uses OpenAI's CUA (Computer Using Agent) to browse YC cofounder profiles, evaluate matches against YOUR criteria, and automatically send connection invites - all from a simple Streamlit dashboard.

## Why now
- OpenAI's CUA model (2025) provides 87% accuracy on browser tasks via Responses API
- No need for complex Playwright scripting - CUA handles all browser interaction via screenshots
- $3/1M input tokens makes it cost-effective for autonomous browsing sessions

## Goals
- **User-centric design**: Input YOUR profile once, set criteria, let CUA find matches for you
- **Fully autonomous browsing**: CUA navigates, screenshots, evaluates, and sends invites
- **Smart matching**: AI evaluates compatibility based on your specific criteria
- **Safety controls**: Quota limits, deduplication, stop button, audit logs
- **Simple dashboard**: Streamlit UI for configuration and monitoring

## Non-Goals (for MVP)
- Manual profile pasting (old approach - we're automating discovery)
- Complex Playwright scripting (CUA handles browser control)
- Multi-site support (focus on YC first)
- Advanced ML ranking (use OpenAI's evaluation for now)

## Success Metrics (MVP)
- Setup time under 10 minutes (just add profile + criteria)
- Autonomous session processes 20+ profiles without intervention
- Match accuracy > 80% (good matches based on criteria)
- Zero duplicate messages (deduplication working)
- Cost < $0.50 per session (CUA token efficiency)

## Stakeholders & Usage
- **Primary user**: Founders seeking cofounders on YC platform
- **Operation mode**: Set profile/criteria → Start CUA → Monitor progress
- **Frequency**: Daily/weekly sessions with 5-10 messages per run

## Technical Approach
- **Browser Control**: OpenAI CUA via Responses API (no Playwright needed)
- **Matching Logic**: OpenAI GPT-4 evaluates profiles against criteria
- **UI**: Streamlit for user profile, criteria, templates, monitoring
- **Storage**: SQLite for deduplication, JSONL for event logs

## User Flow
1. **Setup (one-time)**:
   - Enter your profile (background, skills, vision)
   - Define match criteria (technical skills, domain, location)
   - Customize message template

2. **Run Session**:
   - Click "Start Matching" in Streamlit
   - CUA opens browser, logs into YC
   - CUA browses profiles autonomously
   - For each profile: screenshot → evaluate → send if match

3. **Monitor**:
   - Real-time event log in dashboard
   - Match decisions with explanations
   - Stop button for immediate halt
   - Session summary with stats

## Key Differentiators
- **Autonomous**: No manual profile pasting required
- **Intelligent**: AI-driven matching, not keyword search
- **Transparent**: See why each match was accepted/rejected
- **Safe**: Multiple safeguards against over-messaging
- **Simple**: One dashboard, minimal configuration