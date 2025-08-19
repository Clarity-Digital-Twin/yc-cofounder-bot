YC Co-Founder Autonomous Matching Agent — Documentation

## Purpose
An autonomous matching agent that uses OpenAI's CUA (Computer Using Agent) to browse YC cofounder profiles, evaluate compatibility with YOUR criteria, and automatically send connection invites - all managed from a simple Streamlit dashboard.

## Key Innovation
- **No manual browsing**: CUA autonomously navigates the YC site
- **User-centric**: Enter YOUR profile once, let CUA find matches for you
- **AI-powered matching**: Intelligent evaluation against your specific criteria
- **Fully automated**: From discovery to message sending

## Documentation Structure

### Core Documents (Updated for CUA)
- `01-product-brief.md` — Autonomous matching vision and goals
- `02-scope-and-requirements.md` — User-centric requirements
- `03-architecture.md` — CUA-based system design
- `04-implementation-plan.md` — 3-week CUA integration roadmap
- `10-ui-reference.md` — Streamlit dashboard components

### Supporting Documents
- `05-operations-and-safety.md` — Safety, quotas, compliance
- `06-dev-environment.md` — Development setup
- `07-project-structure.md` — Code organization
- `08-testing-quality.md` — Testing strategy
- `09-roadmap.md` — Future enhancements
- `11-engineering-guidelines.md` — Code standards
- `12-prompts-and-rubric.md` — AI evaluation logic

### User Configuration Files
- `CURRENT_COFOUNDER_PROFILE.MD` — Your profile template
- `MATCH_MESSAGE_TEMPLATE.MD` — Outreach message template
- `WEBSITE_LINK.MD` — Target YC URL

## Quick Start

1. **Setup Your Profile**:
   - Edit `CURRENT_COFOUNDER_PROFILE.MD` with your background
   - Define match criteria in the Streamlit UI
   - Customize message template

2. **Configure API Access**:
   - Get OpenAI API key (tier 3-5 for CUA)
   - Add to `.env` file
   - Verify CUA access with test script

3. **Launch Dashboard**:
   ```bash
   streamlit run src/yc_matcher/interface/web/ui_streamlit.py
   ```

4. **Start Matching**:
   - Click "Start Matching" button
   - CUA opens browser and begins autonomous browsing
   - Monitor progress in real-time event log
   - Review matches and sent messages

## Technical Stack

- **Browser Automation**: OpenAI CUA via Responses API ($3/1M tokens)
- **Matching Logic**: GPT-4 evaluation with structured output
- **UI Framework**: Streamlit for dashboard
- **Storage**: SQLite for deduplication, JSONL for logs
- **Language**: Python 3.12+ with async support

## Architecture Shift

### Old Approach (Manual)
- User pastes candidate profiles one by one
- Evaluates each manually
- Uses Playwright for basic automation

### New Approach (Autonomous)
- User enters their profile once
- CUA browses all profiles automatically
- AI evaluates and sends messages autonomously

## Cost & Performance

- **Cost**: ~$0.50 per 20-profile session
- **Speed**: 30 seconds per profile
- **Accuracy**: 87% browser task success (CUA benchmark)
- **Tokens**: <1000 per profile evaluation

## Safety Features

- Hard quota limits (10 messages/session default)
- Deduplication (never message same person twice)
- Emergency stop button
- Complete audit trail in JSONL
- Rate limiting between actions

## Next Steps

See `04-implementation-plan.md` for detailed roadmap:
1. Week 1: CUA integration and core matching
2. Week 2: Autonomous browsing implementation
3. Week 3: Safety features and testing