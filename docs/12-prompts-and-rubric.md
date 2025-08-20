# 12 — Prompts & Rubric

**Status:** Draft v0.3 (2025-08-20)  
**Owner:** ML/Decision Team  
**Related:** [01-product-brief.md] · [02-scope-and-requirements.md] · [03-architecture.md] · [10-ui-reference.md]

## Goals

1. Define **exact prompts** for:
   - **OpenAI CUA Navigation** (Computer Use via Agents SDK)
   - **Decision Modes**: Advisor (LLM-only), Rubric (deterministic), Hybrid (weighted)
2. Specify **JSON contracts** (stable, testable)
3. Lock **rubric weights**, **thresholding**, **safety gates**, and **observability**

---

## Core Inputs (3 User-Provided)

- **Your Profile** (markdown/free text) → `my_profile`
- **Match Criteria** (must-have/should-have/disqualifiers) → `criteria`  
- **Message Template** (with placeholders) → `template`

---

## Decision Output Contract

All decision modes **MUST** produce this JSON schema (no extra keys, no prose):

```json
{
  "mode": "advisor|rubric|hybrid",
  "decision": "YES|NO",
  "rationale": "string (≤120 chars, no PII)",
  "extracted": {
    "name": "string|null",
    "headline": "string|null",
    "skills": ["string"],
    "interests": ["string"],
    "location": "string|null",
    "stage": "string|null",
    "availability": "string|null",
    "links": ["string"],
    "raw_excerpt": "string (≤400 chars)"
  },
  "scores": {
    "rubric_score": 0.0,
    "llm_confidence": 0.0,
    "final_score": 0.0
  }
}
```

- **YES** if `final_score ≥ THRESHOLD` and all hard rules pass
- `raw_excerpt` is a short profile text slice for audit (no full copy)

---

## Rubric Engine (Deterministic)

### Hard Disqualifiers (Fail Fast)
- Explicit disqualifier from criteria present
- Missing must-have skill/domain/commitment

### Weighted Should-Have Scoring (0-1)
```python
RUBRIC_WEIGHTS = {
    "skill_overlap": 0.35,      # Technical skills/stack match
    "domain_match": 0.20,        # Industry/interest alignment
    "commitment": 0.15,          # FT/PT availability match
    "stage_fit": 0.10,          # Idea/MVP/Revenue alignment
    "location": 0.10,           # Geographic/timezone compatibility
    "signals": 0.10             # Profile completeness/clarity
}
```

### Scoring Functions

#### Skill Overlap (Jaccard Similarity)
```python
def score_skills(user_skills, candidate_skills):
    if not user_skills or not candidate_skills:
        return 0.0
    
    user_set = set(normalize_skills(user_skills))
    candidate_set = set(normalize_skills(candidate_skills))
    
    intersection = user_set & candidate_set
    union = user_set | candidate_set
    
    return len(intersection) / len(union) if union else 0.0
```

#### Location Match
```python
def score_location(user_location, candidate_location):
    # Same city/metro: 1.0
    # Same state/region: 0.7
    # Same country: 0.4
    # Different country but remote-ok: 0.3
    # Otherwise: 0.0
```

#### Final Score Calculation
- **Rubric Mode**: `final_score = rubric_score`
- **Advisor Mode**: `final_score = llm_confidence`
- **Hybrid Mode**: `final_score = α * llm_confidence + (1-α) * rubric_score`

---

## Safety Gates & Thresholds

A message send is eligible **ONLY IF** all conditions are true:

1. `final_score ≥ THRESHOLD` (from env)
2. **Not seen** (check `.runs/seen.sqlite`)
3. **Quota OK** (check `.runs/quota.sqlite`)
4. **STOP flag absent** (`.runs/stop.flag`)
5. `SHADOW_MODE=0` (env var)

On successful send, emit:
```json
{"event": "sent", "ok": true, "mode": "auto", "verified": true, "chars": 312, "retry": 0}
```

---

## OpenAI CUA System Prompt

Used with OpenAI Computer Use (Agents SDK) as the system instructions:

```
ROLE: system
CONTENT:

You are an on-screen operator for YC Cofounder Matching. Follow these rules precisely:

1) Safety & Controls
- Never attempt login storage; user logs in manually if needed
- If a login wall appears: STOP and report "login_required"
- Obey STOP: if instructed, cease all new actions immediately
- Respect pacing and quotas; never send if Shadow Mode is enabled

2) Scope
- Navigate to the configured YC listing URL
- Iterate candidate tiles: open profile → extract visible text → return to listing
- For each profile, collect concise text excerpt and key fields from visible content
- When instructed to message, focus message box, paste draft verbatim, click Send, verify success

3) Accuracy
- Read only visible text on page; do not hallucinate missing data
- If required element cannot be found, report specifically what's missing

4) Non-goals
- No bulk export/scraping beyond per-profile processing
- Do not bypass CAPTCHAs or anti-bot systems

Acknowledge with: READY
```

### CUA Tasklet Examples (User Messages)

**Open Listing**
```
Navigate to this URL and confirm the listing is visible:
{{YC_MATCH_URL}}
```

**Open Next Profile**
```
On the current listing, open the next candidate's profile in the same tab.
```

**Extract Fields**
```
Read the visible profile and return a concise excerpt plus fields:
name, headline, skills[], interests[], location, stage, availability, links[].
Keep the excerpt ≤400 chars. Do not invent data.
```

**Fill & Send Message**
```
Focus the message text box. Paste this draft verbatim (do not edit):
---
{{DRAFT}}
---
Then click the "Send" or "Invite to connect" button and confirm success via visible feedback.
```

---

## Advisor Mode Prompt

System prompt for `OPENAI_DECISION_MODEL`:

```
ROLE: system
CONTENT:

You are a concise evaluator determining cofounder-fit based on:
(A) my_profile (authoritative)
(B) criteria (must/should/disqualifiers)
(C) candidate_profile (extracted text)

Output strict JSON object (no extra keys), conforming to the decision schema.

Rules:
- "decision" is YES only if no hard disqualifiers and candidate matches must-haves
- "llm_confidence" reflects your confidence [0,1]
- "rationale" ≤120 chars, plain language, no PII
- "extracted.raw_excerpt" ≤400 chars from candidate text

No prose outside JSON.
```

**User Message Template:**
```
my_profile:
<<<
{{MY_PROFILE}}
>>>

criteria:
<<<
{{CRITERIA}}
>>>

candidate_profile:
<<<
{{PROFILE_TEXT_EXCERPT}}
>>>
```

---

## Message Template Rendering

### Supported Placeholders
- `{first_name}` - From extracted name field
- `{their_highlight}` - One fact from skills/interests
- `{why_match}` - Connecting criteria to candidate
- `{my_context}` - One-liner from your profile
- `{cta}` - Call to action

### Example Template
```
Hi {first_name} — loved your work on {their_highlight}. 
I'm exploring a cofounder fit around {my_context}.
Looks like strong overlap with {why_match}. 
If you're open, quick chat this week? {cta}
```

### Rendering Rules
- Max 500 characters total
- Strip unresolved placeholders
- Sanitize HTML/scripts
- Preserve line breaks

---

## Event Logging Schema

Append to `events.jsonl`:

```json
// Start
{"event": "start", "run_id": "uuid", "mode": "hybrid", "threshold": 0.72, "alpha": 0.5}

// Profile Read
{"event": "profile_read", "url": "...", "excerpt_len": 384}

// Decision
{"event": "decision", "mode": "hybrid", "scores": {...}, "decision": "YES", 
 "rationale": "Strong ML match", "model": "<from-env>"}

// Sent
{"event": "sent", "ok": true, "mode": "auto", "verified": true, "chars": 312}

// Model Usage
{"event": "model_usage", "provider": "openai", "model": "<from-env>", 
 "tokens_in": 1200, "tokens_out": 150, "cost_est": 0.042}

// Quota
{"event": "quota", "day_count": 15, "week_count": 67, "allowed": true}

// Stop
{"event": "stop", "reason": "user_requested"}

// Error
{"event": "error", "where": "cua_init", "message": "...", "retryable": true}
```

---

## Acceptance Criteria (Prompt-Level)

- **AC-D1**: CUA replies "READY" on system init
- **AC-D2**: Extract returns name/headline plus ≤400 char excerpt
- **AC-D3**: Advisor returns valid JSON only (no stray text)
- **AC-D4**: Hybrid math correct (α=0.5, scores 0.6/0.8 → 0.7)
- **AC-D5**: Shadow mode prevents all sends
- **AC-D6**: STOP flag halts within ≤2s
- **AC-D7**: Dedupe prevents re-sending to seen profiles

---

## Configuration Reference

```env
# Engines
ENABLE_CUA=1
ENABLE_PLAYWRIGHT_FALLBACK=1
ENABLE_PLAYWRIGHT=0

# OpenAI
OPENAI_API_KEY=sk-...
CUA_MODEL=<your-computer-use-model>      # From Models endpoint
CUA_TEMPERATURE=0.3
CUA_MAX_TOKENS=1200

# Decision
DECISION_MODE=hybrid                     # advisor|rubric|hybrid
OPENAI_DECISION_MODEL=<your-best-llm>    # For Advisor/Hybrid
THRESHOLD=0.72
ALPHA=0.50

# Runtime & Safety
YC_MATCH_URL=https://www.startupschool.org/cofounder-matching
SEND_DELAY_MS=5000                       # Milliseconds between sends
DAILY_QUOTA=25
WEEKLY_QUOTA=120
SHADOW_MODE=0
```

---

## Integration with OpenAI CUA

```python
from agents import Agent, ComputerTool, Session  # package: openai-agents

class CUANavigator:
    def __init__(self):
        self.agent = Agent(
            tools=[ComputerTool()],
            model=os.getenv("CUA_MODEL"),  # Never hardcode
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=float(os.getenv("CUA_TEMPERATURE", "0.3"))
        )
        self.session = Session()
    
    async def extract_profile(self):
        result = await self.session.run(
            self.agent,
            EXTRACT_FIELDS_PROMPT
        )
        return parse_cua_response(result.content)
```

---

## Invariants (Non-Negotiable)

1. **CUA is primary**; Playwright only if CUA unavailable/fails and fallback enabled
2. **No send** if STOP, quota exceeded, seen duplicate, or Shadow Mode
3. Always log `decision` before any `sent` event
4. No `$HOME` writes; all caches under repo
5. No storing credentials or full screenshots
6. Models from environment variables only (never hardcoded)
7. Use `SEND_DELAY_MS` for pacing (not PACE_MIN_SECONDS)

---

## Version History

- v0.3 (2025-08-20): Fixed env vars, added acceptance criteria, detailed schemas
- v0.2 (2025-08-20): Added OpenAI CUA integration, removed Anthropic references
- v0.1 (2025-08-19): Initial draft

---

**Key Changes from External Audit:**
- ✅ Added structured JSON contracts and acceptance criteria
- ✅ Added ready-to-use CUA tasklets
- ✅ Detailed rubric weights and scoring functions
- ❌ Fixed WRONG env var (PACE_MIN_SECONDS → SEND_DELAY_MS)
- ❌ Kept as Draft (not "Final v1.0")
- ✅ Added actual code integration example