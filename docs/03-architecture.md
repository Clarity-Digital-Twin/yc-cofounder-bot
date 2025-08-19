Architecture

## Principles
- Keep orchestration minimal; leverage OpenAI's CUA (Computer Using Agent) via Responses API.
- User-centric flow: User profile → Match criteria → CUA autonomous browsing → Auto-send messages.
- Use simple local storage (SQLite/JSON) for deduplication and quota tracking.
- Adopt DDD layering: Domain (pure) → Application (use cases) → Infrastructure (adapters) → Interface (UI/CLI).
- CUA handles all browser interaction via screenshots and mouse/keyboard actions (no Playwright needed).

## High-Level Components (mapped to DDD layers)
- **Domain:**
  - Entities/VOs: UserProfile, MatchCriteria, CandidateProfile, Decision, Score.
  - Domain Services: MatchingService (evaluates candidate against user's criteria).
- **Application:**
  - Use Cases: EvaluateMatch, SendInvite, ProcessCandidates.
  - Ports: DecisionPort, MatchingPort, MessagePort, QuotaPort, SeenRepo, LoggerPort, CUAPort.
- **Infrastructure:**
  - OpenAICUAAdapter implements CUAPort using CUA model via Responses API.
  - OpenAIDecisionAdapter implements DecisionPort for match evaluation.
  - SQLiteSeenRepo implements SeenRepo for deduplication.
  - JSONLLogger implements LoggerPort for event tracking.
  - TemplateRenderer implements MessagePort with personalization.
- **Interface:**
  - Streamlit UI: User profile input, criteria settings, template editor, start/stop controls.
  - DI factories to wire ports to use cases.
- **Config & Secrets:**
  - `.env` for OPENAI_API_KEY; app args for run-time overrides.
- **Persistence:**
  - SQLite: `seen_profiles` (hash, ts), `runs`, `events`; session logs and dedupe.

## Data Flow (Autonomous Matching with CUA)
1) **User Setup**: Enter YOUR profile + ideal match criteria + message template in Streamlit.
2) **CUA Navigation**: CUA opens YC site → logs in → navigates to cofounder matching page.
3) **Profile Discovery**: CUA scrolls through candidate list → takes screenshots → clicks "View profile".
4) **Match Evaluation**: Backend evaluates candidate profile against user's criteria → calculates match score.
5) **Auto-Send**: If match score > threshold → CUA fills message form with template → clicks "Invite to connect".
6) **Tracking**: Logger writes events; SQLite tracks sent profiles; respects quota limits.

## Key Configs
- **Model**: CUA (Computer Using Agent) via OpenAI Responses API
- **Pricing**: $3/1M input tokens, $12/1M output tokens
- **API**: Responses API with computer_use tool (tier 3-5 developers)
- **Display**: 1280×800 recommended for stable screenshots
- **Timeouts**: per-step wait 0.5–2s; max overall runtime configurable
- **Quota**: integer per session; default 5-10 messages

## CUA Technical Details
- **Perception**: Takes screenshots to understand current screen state
- **Reasoning**: Chain-of-thought reasoning to plan next actions
- **Actions**: Generates mouse clicks, keyboard input, scrolling
- **Performance**: 87% accuracy on WebVoyager browser tasks
- **Safety**: Requires tier 3-5 API access; not for high-stakes tasks

## Security & Privacy
- No credentials stored in prompts or logs.
- CUA operates in isolated browser context.
- Local `.env` for API keys, not committed to git.
- Audit trail via JSONL event logs.

## Extensibility
- Swap CUA for Playwright for non-AI automation.
- Add multiple matching sites beyond YC.
- Integrate with CRM for lead tracking.
- Add ML-based profile ranking for better matches.