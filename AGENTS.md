# AGENTS.md - AI Assistant Guide

This file provides guidance for AI assistants (Claude, GPT, etc.) working with this codebase.

## Quick Start

This is a YC Co-Founder Matching Bot that uses OpenAI's Computer Use API (via Responses API) combined with Playwright for browser automation.

## Current State (December 2025)

✅ **Working & Fixed:**
- OpenAI Responses API integration for GPT-5 with proper reasoning item handling
- CUA browser implementation via Responses API + Playwright
- Decision engine supporting AI/Rubric/Hybrid modes
- Response parsing correctly uses `output_text` helper
- CLI tools updated to use Responses API

❌ **Not Using (Legacy):**
- OpenAI Agents SDK (removed - use Responses API)
- Chat Completions for GPT-5 (use Responses API)
- Beta Assistants API (not needed)

## Key Implementation Details

### GPT-5 Response Parsing (CRITICAL)
```python
# Correct - use output_text helper first
if hasattr(response, "output_text"):
    content = response.output_text
else:
    # Manual parsing - skip reasoning items!
    for item in response.output:
        if item.type == "reasoning":
            continue  # Skip reasoning
        if item.type == "message":
            # Extract text from message content
```

### CUA Integration Pattern
```python
# 1. Call Responses API with computer_use_preview tool
resp = client.responses.create(
    model="computer-use-model",
    tools=[{"type": "computer_use_preview", ...}],
    input=[...],
    max_output_tokens=800  # NOT max_tokens!
)

# 2. Execute actions with Playwright
if resp has computer_call:
    await playwright.execute(action)
    
# 3. Send screenshot back
client.responses.create(
    previous_response_id=resp.id,
    computer_call_output={...}
)
```

## Common Pitfalls to Avoid

1. **Don't use Agents SDK** - It's deprecated. Use Responses API.
2. **Don't parse responses manually without checking reasoning** - GPT-5 includes reasoning items
3. **Don't use max_tokens** - Use `max_output_tokens` for Responses API
4. **Don't use chat.completions for GPT-5** - Use Responses API
5. **Don't forget previous_response_id** - Chain turns in CUA conversations

## Testing & Verification

```bash
# Verify setup
make check-cua    # Tests Responses API access
make test         # Run unit tests
make verify       # Full validation

# Required environment
OPENAI_API_KEY=sk-...
CUA_MODEL=<your-cua-model>
OPENAI_DECISION_MODEL=gpt-5  # or gpt-4
```

## Architecture Reference

- `openai_decision.py` - LLM decision making via Responses/Chat API
- `openai_cua_browser.py` - CUA + Playwright browser control
- `check_cua.py` - CLI to verify Responses API access
- All use Responses API for GPT-5, fallback to Chat for GPT-4

## Getting Help

Check these files for details:
- `CLAUDE.md` - Full project documentation
- `GPT5_FACTS.md` - GPT-5 specific details
- `docs/` - Architecture and design docs