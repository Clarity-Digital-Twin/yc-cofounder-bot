# INDEPENDENT AUDIT PROMPT FOR FRESH AI AGENT

## 🎯 MISSION CRITICAL AUDIT REQUEST

You are tasked with performing a **comprehensive independent audit** of a YC Cofounder Matching Bot codebase that claims to use OpenAI Computer Use API (CUA) and GPT-5 for autonomous browser automation. The team wants to launch on Hacker News but needs verification that everything is actually working as documented.

## 📋 YOUR AUDIT OBJECTIVES

### Phase 1: Documentation Reality Check (30 mins)
1. **Read ALL documentation in this exact order:**
   - `README.md` - Understand what this app claims to do
   - `CLAUDE.md` - Development guidelines and architecture claims
   - `SSOT.md` - Single Source of Truth (may be outdated)
   - `CANONICAL_TRUTH.md` - What they think is correct
   - `AUDIT_AND_PLAN.md` - Their own audit findings
   - `FINAL_TRUTH.md` - Their "final" understanding
   - `MODEL_RESOLUTION_IMPLEMENTED.md` - Recent changes

2. **Extract contradictions and gaps:**
   - List every contradiction between documents
   - Identify claims that seem impossible (e.g., "GPT-5-thinking" in August 2025)
   - Note any architectural decisions that don't make sense
   - Flag any "we'll implement this later" items

### Phase 2: Code Truth Verification (45 mins)
3. **Verify OpenAI CUA Implementation:**
   ```bash
   # Check if they're actually using Responses API or old Agents SDK
   grep -r "responses.create" src/
   grep -r "Agent(" src/
   grep -r "computer_use_preview" src/
   ```
   - File: `src/yc_matcher/infrastructure/openai_cua_browser.py`
   - **CRITICAL**: Are they using `client.responses.create()` with `previous_response_id` chaining?
   - Or are they using deprecated `Agent()` class from agents SDK?
   - Is Playwright actually executing the actions or is it just claims?

4. **Verify Model Resolution:**
   ```bash
   # Check how models are actually selected
   cat src/yc_matcher/infrastructure/model_resolver.py
   cat src/yc_matcher/infrastructure/openai_decision.py
   ```
   - Does model discovery actually work via `client.models.list()`?
   - What happens when GPT-5 doesn't exist? (Spoiler: It probably doesn't)
   - Are they hardcoding models despite claiming dynamic resolution?

5. **Verify Browser Automation:**
   ```bash
   # Check browser singleton pattern
   cat src/yc_matcher/infrastructure/browser_playwright_async.py
   cat src/yc_matcher/infrastructure/async_loop_runner.py
   ```
   - Is there actually a singleton pattern preventing multiple browsers?
   - Does auto-login work with the YC credentials in `.env`?
   - Can it navigate from dashboard to profiles?

6. **Verify 3-Input Flow:**
   ```bash
   # Check if template actually goes to NLP
   grep -A 20 "Message Template" src/yc_matcher/interface/web/ui_streamlit.py
   grep -A 20 "MESSAGE_TEMPLATE" src/yc_matcher/infrastructure/openai_decision.py
   ```
   - Does the message template actually get sent to the NLP model?
   - Or does it bypass NLP and just get pasted directly?

### Phase 3: Test Suite Analysis (30 mins)
7. **Run and analyze tests:**
   ```bash
   make test           # Unit tests
   make test-int       # Integration tests
   make verify         # Full verification
   ```
   - How many tests actually pass?
   - Are critical paths tested (CUA loop, browser singleton, decision flow)?
   - Any tests for the claimed features that are skipped/mocked?

8. **Check test coverage of critical features:**
   - Is there a test for CUA Responses API loop?
   - Is there a test for browser singleton pattern?
   - Is there a test for model resolution fallback?
   - Is there a test for the 3-input flow?

### Phase 4: Feature Completeness Audit (45 mins)
9. **Test each claimed feature:**
   ```bash
   # Start the app
   make run
   ```
   Then verify:
   - [ ] Can you actually input Profile, Criteria, and Message Template?
   - [ ] Does clicking "Start Autonomous Browsing" work without errors?
   - [ ] Does it auto-login to YC with stored credentials?
   - [ ] Does it navigate to candidate profiles?
   - [ ] Does it evaluate profiles using AI?
   - [ ] Does it generate personalized messages (not just template)?
   - [ ] Does it actually send messages (in shadow mode first)?

10. **OpenAI API Integration Verification:**
    ```bash
    python scripts/test_model_resolution.py
    python scripts/test_decision_engine.py
    python scripts/check_cua.py
    ```
    - Which models are actually available on this account?
    - Does Computer Use work or return errors?
    - Is GPT-5 real or are they using GPT-4?

### Phase 5: Production Readiness Assessment (30 mins)
11. **Security & Safety:**
    - Are YC credentials properly secured?
    - Is there a working STOP mechanism?
    - Are quotas actually enforced?
    - Can it accidentally spam people?

12. **Performance & Reliability:**
    - Single browser instance actually maintained?
    - Memory leaks from Playwright?
    - Proper error handling and recovery?
    - Rate limiting respected?

## 📝 DELIVERABLES REQUIRED

Create these files with your findings:

### 1. `INDEPENDENT_AUDIT_RESULTS.md`
```markdown
# Independent Audit Results
Date: [Date]
Auditor: [AI Agent Name]

## Executive Summary
- Overall Status: [NOT READY / ALMOST READY / READY] for Hacker News
- Critical Issues: [count]
- Major Issues: [count]
- Minor Issues: [count]

## Critical Findings

### 1. OpenAI CUA Implementation
**Status**: [WORKING / BROKEN / PARTIALLY WORKING]
**Evidence**: [specific code references]
**Reality**: [what's actually implemented vs claimed]

### 2. Model Resolution
**Status**: [...]
**Available Models**: [actual list from API]
**GPT-5 Reality Check**: [does it exist on this account?]

### 3. Browser Automation
[...]

### 4. Three-Input Flow
[...]

## What's Actually Working
- [List everything that genuinely works]

## What's Completely Broken
- [List with evidence]

## What's Half-Implemented
- [List with specific gaps]
```

### 2. `REFACTOR_PRIORITY_LIST.md`
```markdown
# Refactoring Priority List

## P0 - Blockers (Must fix before HN launch)
1. [Issue] - [File:line] - [Estimated effort]

## P1 - Critical (Should fix)
1. [Issue] - [File:line] - [Estimated effort]

## P2 - Nice to Have
1. [Issue] - [File:line] - [Estimated effort]
```

### 3. `TRUE_ARCHITECTURE.md`
```markdown
# True Architecture (What's Actually Built)

## Real Implementation Status

### OpenAI Integration
- Decision Model: [actual model being used]
- CUA Model: [actual model or "not working"]
- API Pattern: [Responses API / Agents SDK / Chat Completions]

### Browser Control
- Pattern: [Singleton / Multiple instances / Broken]
- Auto-login: [Working / Broken]
- Navigation: [Working / Broken]

### Data Flow
[Actual flow diagram with truth]
```

### 4. `HACKER_NEWS_READINESS.md`
```markdown
# Hacker News Launch Readiness

## Demo Video Script
[What actually works that we can show]

## Known Limitations to Disclose
[What we should be honest about]

## Minimum Fixes Required
[What absolutely must work]

## Suggested Tagline
[Based on what actually works]
```

## 🔍 INVESTIGATION COMMANDS

Run these commands to understand the truth:

```bash
# 1. Find all TODOs and FIXMEs
grep -r "TODO\|FIXME\|XXX\|HACK" src/

# 2. Find all try/except blocks that might hide errors  
grep -r "except.*pass" src/
grep -r "except Exception" src/

# 3. Check for hardcoded values despite claims of dynamic
grep -r "gpt-5\|gpt-4" src/
grep -r "computer-use-preview" src/

# 4. Find mocked/stubbed code
grep -r "mock\|stub\|fake\|dummy" src/ tests/

# 5. Check actual API calls being made
grep -r "client\." src/ | grep -v "#"

# 6. See what's actually in .env
cat .env | grep -v PASSWORD

# 7. Check if browser actually stays single instance
grep -r "_shared\|singleton\|instance" src/

# 8. Verify the UI actually has 3 input fields
grep -r "text_area\|text_input" src/yc_matcher/interface/web/

# 9. Check if tests are actually testing or just passing
grep -r "assert True\|pass.*#.*TODO" tests/

# 10. Find any admission of non-working features
grep -r "not implemented\|doesn't work\|broken" . --include="*.md"
```

## ⚠️ CRITICAL QUESTIONS TO ANSWER

1. **Is OpenAI CUA actually implemented or just planned?**
   - Look for `responses.create()` with computer_use tools
   - Check if actions are executed by Playwright after CUA responds

2. **Does GPT-5 exist on this account or is it GPT-4?**
   - Run model resolution test
   - Check what model is actually being used in logs

3. **Is the browser singleton working or opening multiple windows?**
   - Check AsyncLoopRunner implementation
   - Look for global state management

4. **Does the message template go to NLP or bypass it?**
   - Trace the data flow from UI to decision engine
   - Check if template is in the NLP prompt

5. **Can this actually run autonomously or does it need manual intervention?**
   - Check for HIL (Human-in-loop) blocks
   - Verify auto-login and navigation work

## 🎯 SUCCESS CRITERIA

For this app to be Hacker News ready:
- [ ] Can demo full flow: Input → Browse → Evaluate → Message (even if in shadow mode)
- [ ] Single browser window (no popups)
- [ ] Auto-login works reliably
- [ ] Navigates to profiles successfully
- [ ] Evaluates with real AI model (even if GPT-4)
- [ ] Generates personalized messages (not just templates)
- [ ] Has working safety mechanisms (stop flag, quotas)
- [ ] Can run for 10+ profiles without crashing

## 📊 FINAL VERDICT TEMPLATE

After your audit, provide a clear verdict:

```
VERDICT: [SHIP IT / FIX FIRST / NOT READY]

If SHIP IT:
- Here's your HN post title: [...]
- Here's what to demo: [...]
- Here's what to caveat: [...]

If FIX FIRST:
- Must fix: [list]
- Time estimate: [hours]
- Then ship with: [adjusted claims]

If NOT READY:
- Critical gaps: [list]
- Realistic timeline: [days/weeks]
- Pivot suggestion: [simpler MVP]
```

---

## START YOUR AUDIT NOW

Begin with Phase 1 and work systematically through each phase. Be brutally honest - the team wants truth, not comfort. They need to know if this is ready for Hacker News or if it needs more work.

Your audit will determine whether they launch or fix. No sugar-coating. Just facts and evidence.

Good luck, auditor. The team is counting on your independent assessment.