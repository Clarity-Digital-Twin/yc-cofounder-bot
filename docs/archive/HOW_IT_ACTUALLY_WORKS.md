# HOW THE SYSTEM ACTUALLY WORKS

## TWO SEPARATE AI SYSTEMS:

### 1. NAVIGATION AI (Browser Control)
**Currently:** Playwright with hardcoded selectors (ENABLE_CUA=0)
**Optional:** OpenAI Computer Use API (ENABLE_CUA=1)

- **Model:** `computer-use-preview` (when CUA enabled)
- **Purpose:** SEE screenshots, CLICK buttons, NAVIGATE pages
- **How:** Takes screenshot → AI suggests "click at (x,y)" → Playwright executes

### 2. DECISION AI (Match Evaluation) 
**Model:** `gpt-5-thinking` (NEW August 2025 model!)
**Purpose:** READ profiles, DECIDE yes/no, WRITE messages

This is like your ChatGPT workflow:
```
Input: "Here's a candidate profile: [text]
        Here's my criteria: [requirements]
        Should I match? If yes, write a message"

Output: {
  decision: "YES",
  rationale: "Strong Python/FastAPI match, healthcare experience...",
  draft: "Hey John, your FastAPI work caught my eye..."
}
```

## THE COMPLETE FLOW:

1. **Playwright** opens browser, auto-logs in
2. **Playwright** clicks "View Profiles" 
3. **Playwright** extracts profile text
4. **GPT-5-thinking** evaluates match (via API)
5. **GPT-5-thinking** generates message
6. **Playwright** pastes message and sends
7. **Playwright** skips to next profile
8. REPEAT

## WHY TWO MODELS?

- **Computer Use API** = Good at SEEING and CLICKING (visual AI)
- **GPT-5-thinking** = Good at REASONING and WRITING (language AI)

They work together:
- CUA handles the browser (when enabled)
- GPT-5 handles the thinking

## CURRENT CONFIG:

```env
# Navigation
ENABLE_CUA=0                    # OFF - using Playwright selectors
CUA_MODEL=computer-use-preview  # Would use this if enabled

# Decisions  
OPENAI_DECISION_MODEL=gpt-5-thinking  # Smart matching!
DECISION_MODE=hybrid                  # Rubric filter + GPT-5
```

## TO TEST CUA:

```bash
# Enable Computer Use for navigation
ENABLE_CUA=1 python test_everything_works.py
```

## TO TEST DECISIONS:

```bash
# Should generate actual messages now with GPT-5
SHADOW_MODE=0 python test_everything_works.py
```

## THE PROBLEM WE NEED TO FIX:

The decision engine isn't properly calling GPT-5-thinking to generate messages. It's returning YES but no draft. Need to fix the API call to actually generate the message template.
# DEPRECATED (December 2025)
This file is archived and may contain outdated OpenAI API guidance.
For the single source of truth, see `OPENAI_API_REFERENCE.md` and `CONTEXT7_TRUTH.md`.
Do not rely on this file for current parameters or model IDs.
