# Key Information Extracted from Archive Docs
*Before deleting historical documentation*

## Critical Implementation Details

### YC-Specific Browser Selectors (Working)
From the fixes documentation, these selectors work with YC's interface:
```python
# Message textarea
textarea_selector = "textarea[placeholder*='excited about potentially working' i]"

# Send button
send_button_selector = "button:has-text('Invite to connect')"

# Profile detection
profile_url_pattern = "/candidate/" or "/profile/"
```

### Login Flow Requirements
- YC requires login before accessing profiles
- After login, redirects to `/candidate/[ID]` (already on a profile)
- No need to click "View Profile" when already on profile page
- Implementation: Check if URL contains `/candidate/` and skip clicking

### GPT-5/Responses API Lessons (Even if fictional)
The docs claim these were "working":
1. **Temperature must be 1** for GPT-5 (not 0.7 or 0)
2. **Response parsing**: Skip `reasoning` items, look for `message` items
3. **Fallback approach**: Try with optional params, then without
4. **Output extraction**: Use `output_text` helper first, manual parsing as fallback

### Architecture Insights
1. **Async/Sync Bridge**: AsyncLoopRunner pattern to handle Playwright async in sync context
2. **Singleton Browser**: Share one browser instance across all operations
3. **Decision Flow**: Rubric gate → AI evaluation → Message generation
4. **Event Logging**: Every action emits JSONL events for audit trail

### What Actually Works (Verified)
✅ Playwright browser automation
✅ Login and navigation to profiles
✅ `/candidate/` URL detection
✅ Text extraction from profiles
✅ Safety mechanisms (quotas, dedup, stop flags)
✅ Three decision modes logic (Advisor/Rubric/Hybrid)

### What Doesn't Work
❌ `client.responses.create()` - OpenAI SDK doesn't have this
❌ Computer Use API - not publicly available
❌ GPT-5 model - may not be accessible

### Environment Variables That Matter
```bash
# Working configuration
ENABLE_CUA=0                    # Keep disabled (doesn't exist)
ENABLE_PLAYWRIGHT=1             # Use this
ENABLE_PLAYWRIGHT_FALLBACK=1   # Good fallback
PLAYWRIGHT_HEADLESS=0           # Show browser for debugging

# Login (optional automation)
YC_EMAIL=your_email
YC_PASSWORD=your_password
```

### Critical Bugs Already Fixed
1. **Profile detection**: `/candidate/` check implemented
2. **Message box selector**: Updated for YC's actual UI
3. **Send button text**: "Invite to connect" not just "Send"
4. **Auto-login flow**: Implemented but needs credentials

### Testing Insights
- All tests used mocks, never real API
- Mocks assumed ideal responses, not reality
- No integration tests with actual browser
- "Working" claims based on mocked tests

## Summary
The codebase has solid architecture and Playwright implementation. The main fiction is the "Responses API" that doesn't exist in OpenAI SDK. With proper API calls (chat.completions) and Playwright-only mode, this should work.