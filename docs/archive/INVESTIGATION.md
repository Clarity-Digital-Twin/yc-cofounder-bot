# Investigation: Why The Bot Isn't Working

## The Problem
When clicking "Start Autonomous Browsing", we get:
```
Executable doesn't exist at /home/jj/.cache/ms-playwright/chromium-1181/chrome-linux/chrome
```

## Root Cause Analysis

### 1. Environment Variable Not Propagating
- We set `PLAYWRIGHT_BROWSERS_PATH=.ms-playwright` 
- But Playwright looks in `~/.cache/ms-playwright`
- The env var isn't reaching the async context

### 2. Async/Sync Mismatch
```python
# AutonomousFlow calls (SYNC):
browser.open(url)

# OpenAICUABrowser has (SYNC wrapper):
def open(self, url):
    asyncio.run(self._open_async(url))

# Which calls (ASYNC):
async def _open_async(self, url):
    await self._ensure_browser()  # <-- Creates new event loop
```

### 3. The Browser Path Issue
In `_ensure_browser()`, Playwright starts WITHOUT the env var:
```python
# BEFORE (broken):
self.playwright = await async_playwright().start()
# Now Playwright is initialized with default paths!

# AFTER (fixed):
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
self.playwright = await async_playwright().start()
# Now it knows where to look!
```

## Why It's "Simple" But Not Working

### Conceptually Simple:
1. Open browser
2. Click profiles
3. Read text
4. Evaluate
5. Send or skip

### Implementation Complexity:
1. **Clean Architecture** = Many abstraction layers
2. **Async/Sync mixing** = Event loop issues
3. **Environment variables** = Not propagating correctly
4. **Browser paths** = Looking in wrong location
5. **Safety mechanisms** = Multiple checks and validations

## The Current State

### What Works:
- UI loads ✓
- Decision engine configured ✓
- Storage/logging ready ✓
- Safety mechanisms active ✓

### What's Broken:
- Browser won't launch ✗
- Path configuration issue ✗

### What We Fixed:
1. Added browser path setting BEFORE playwright init
2. Added .claude/ to .gitignore to prevent API key leaks

## Next Steps

1. **Install browsers in correct location**:
   ```bash
   PLAYWRIGHT_BROWSERS_PATH=.ms-playwright uv run python -m playwright install chromium
   ```

2. **Test browser launch**:
   ```bash
   uv run python tests/test_browser_manual.py
   ```

3. **Then try the UI again**

## The Lesson

Even "simple" bots have complex implementation details:
- Path configurations
- Async/sync boundaries  
- Environment variable propagation
- Security (API keys, etc.)

The CONCEPT is simple. The IMPLEMENTATION has gotchas.