# CANONICAL TRUTH - NO DEVIATION ALLOWED

## 🚨 TWO APIs, TWO MODELS, NO CONFUSION

### 1. COMPUTER USE API (Navigation)
- **Model**: `computer-use-preview` 
- **API**: OpenAI Responses API
- **Purpose**: Plans browser actions (click, type, scroll)
- **How**: Takes screenshots → Suggests actions → Playwright executes

### 2. GPT-5-THINKING (Decisions)
- **Model**: `gpt-5-thinking` ONLY (NEVER GPT-4!)
- **API**: OpenAI Chat Completions API
- **Purpose**: Evaluates profiles, generates messages
- **Returns**: `{decision: "YES/NO", rationale: "...", draft: "..."}`

## ⚠️ NEVER USE THESE MODELS
- ❌ gpt-4
- ❌ gpt-4o
- ❌ gpt-4.1
- ❌ gpt-4-turbo
- ❌ ANY GPT-4 variant

## ✅ ONLY USE THESE MODELS
- ✅ gpt-5-thinking (for decisions)
- ✅ gpt-5 (alternative if gpt-5-thinking unavailable)
- ✅ computer-use-preview (for browser navigation)

## THE CORRECT FLOW

```mermaid
graph LR
    A[Start] --> B[Computer Use API]
    B --> C[Plans: "Click View Profile"]
    C --> D[Playwright Executes]
    D --> E[Extract Profile Text]
    E --> F[GPT-5-THINKING API]
    F --> G[Decision + Message]
    G --> H[Send or Skip]
```

## CONFIGURATION (CANONICAL)

```env
# COMPUTER USE (Navigation)
ENABLE_CUA=1                          # Enable Computer Use
CUA_MODEL=computer-use-preview        # OpenAI's CUA model
CUA_MAX_TURNS=40                      # Safety limit

# GPT-5-THINKING (Decisions)
ENABLE_OPENAI=1
OPENAI_DECISION_MODEL=gpt-5-thinking  # GPT-5-THINKING ONLY!
DECISION_MODE=hybrid                  # Rubric + GPT-5

# NEVER CHANGE THESE MODELS
```

## HOW IT WORKS

### When ENABLE_CUA=1 (Full AI Mode)
1. **Computer Use API** looks at screenshot
2. **Computer Use API** says "click at (400, 200)"
3. **Playwright** executes the click
4. **Playwright** takes new screenshot
5. Back to step 1 until profile text extracted
6. **GPT-5-THINKING** evaluates profile
7. **GPT-5-THINKING** generates personalized message

### When ENABLE_CUA=0 (Playwright Only)
1. **Playwright** uses hardcoded selectors
2. **Playwright** extracts profile text
3. **GPT-5-THINKING** evaluates profile
4. **GPT-5-THINKING** generates personalized message

## THE TRUTH ABOUT COMPUTER USE

**Computer Use DOES NOT control browsers directly!**
- CUA = The brain (plans actions)
- Playwright = The hands (executes actions)
- They work TOGETHER

## THE TRUTH ABOUT GPT-5-THINKING

**GPT-5-THINKING is the ONLY model for decisions!**
- Released: August 2025
- Purpose: Advanced reasoning and text generation
- Cost: Worth it for quality matches
- Alternative: gpt-5 (if gpt-5-thinking unavailable)

## COMMON MISTAKES TO AVOID

1. **WRONG**: "Let's use GPT-4 for decisions"
   - **RIGHT**: Always use GPT-5-THINKING

2. **WRONG**: "Computer Use controls the browser"
   - **RIGHT**: Computer Use plans, Playwright executes

3. **WRONG**: "We don't need Playwright with CUA"
   - **RIGHT**: CUA always needs Playwright to execute

4. **WRONG**: "GPT-4 is good enough"
   - **RIGHT**: GPT-5-THINKING or nothing

## TEST COMMANDS

```bash
# Check your models
uv run python scripts/check_models.py

# Test GPT-5-THINKING
uv run python scripts/test_decision_engine.py

# Full test with both APIs
ENABLE_CUA=1 uv run python scripts/run_full_test.py
```

## IF SOMEONE SUGGESTS GPT-4

**NO. NEVER. ABSOLUTELY NOT.**

We use:
- `computer-use-preview` for navigation
- `gpt-5-thinking` for decisions

End of discussion.

---

**This is canonical. This is final. No debates.**