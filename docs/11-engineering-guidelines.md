# 11 — Engineering Guidelines

**Status:** Draft v0.3 (2025-08-20)  
**Owner:** Engineering Team  
**Related:** [03-architecture.md] · [07-project-structure.md] · [08-testing-quality.md]

## Product Truth (The North Star)

**3 inputs → CUA-first autonomy → safe fallback → auditable events**

The system takes exactly **three user inputs**:
1. **Your Profile** (who you are, what you bring)
2. **Match Criteria** (what you're looking for)
3. **Message Template** (how to introduce yourself)

Then **OpenAI Computer Use (CUA)** plans actions from screenshots and we execute them locally with **Playwright**. Playwright-only is used as fallback when CUA is unavailable.

## Architecture Principles

### Domain-Driven Design (DDD)
- **Domain Layer**: Pure business logic, no external dependencies
- **Application Layer**: Use cases orchestrating domain + ports
- **Infrastructure Layer**: Adapters implementing ports (CUA, Playwright, OpenAI, SQLite)
- **Interface Layer**: Entry points (Streamlit UI, CLI) with dependency injection

### Clean Architecture Flow
```
Interface → Application → Domain
    ↓           ↓
Infrastructure ←┘
```

### Ports & Adapters (Hexagonal)
Define contracts as abstract ports; swap implementations without touching business logic:
- **BrowserPort**: Implemented by `OpenAICUABrowser` (primary) or `PlaywrightBrowser` (fallback)
- **DecisionPort**: Implemented by Advisor/Rubric/Hybrid modes
- **LoggerPort**: Implemented by JSONL logger
- **QuotaPort/SeenRepo**: Implemented by SQLite repositories

## Coding Standards

### Import Conventions
```python
# OpenAI Computer Use (Responses API)
from openai import OpenAI
client = OpenAI()

# Use Responses API with computer_use tool; execute actions with Playwright

# Standard library
import os
from typing import Optional, Dict, Any

# Domain imports (relative within layer)
from ..domain.entities import Profile, Decision
from ..application.ports import BrowserPort
```

### Type Hints & Documentation
- **Required** in domain/ and application/ layers
- Use pydantic for DTOs and external data validation
- Docstrings for public methods with examples

### Error Handling
```python
# Explicit about failures
try:
    result = await browser.send_message(text)
    if not result.verified:
        raise MessageNotSentError(f"Verification failed: {result.reason}")
except CUAUnavailableError:
    # Fallback to Playwright if enabled
    if self.enable_playwright_fallback:
        result = await self.playwright_browser.send_message(text)
```

### No Global State
- Pass dependencies explicitly via constructors
- Use dependency injection container in interface layer
- Environment variables only read in config module

## Repo-Scoped Execution (No $HOME Writes)

**Critical invariant**: Nothing writes to `$HOME` or system directories.

```bash
# Enforced in Makefile
export UV_CACHE_DIR=.uv_cache
export XDG_CACHE_HOME=.cache
export PLAYWRIGHT_BROWSERS_PATH=.ms-playwright
export MPLCONFIGDIR=.mplconfig
export UV_LINK_MODE=copy

# Streamlit sandboxing
export HOME="$PWD/.home"
```

## Port Definitions

### BrowserPort (Primary Contract)
```python
class BrowserPort(Protocol):
    async def open(self, url: str) -> None:
        """Navigate to URL"""
    
    async def read_profile_text(self) -> str:
        """Extract visible profile text"""
    
    async def focus_message_box(self) -> None:
        """Focus the message input area"""
    
    async def fill_message(self, text: str) -> None:
        """Type message into focused area"""
    
    async def click_send(self) -> None:
        """Click the send button"""
    
    async def verify_sent(self) -> bool:
        """Verify message was sent successfully"""
    
    async def close(self) -> None:
        """Clean up resources"""
```

### OpenAICUABrowser Implementation (planner + executor)
```python
from openai import OpenAI

class OpenAICUABrowser:
    def __init__(self):
        self.client = OpenAI()
        self.model = os.getenv("CUA_MODEL")
        # Playwright page initialized elsewhere; used to execute actions and take screenshots

    async def plan_and_act(self, instruction: str) -> None:
        resp = self.client.responses.create(
            model=self.model,
            input=[{"role": "user", "content": instruction}],
            tools=[{"type": "computer_use_preview", "display_width": 1280, "display_height": 800}],
            truncation="auto",
            previous_response_id=self.prev_id,
        )
        # If resp includes a computer_call, execute via Playwright, take a screenshot,
        # then send computer_call_output and loop until done.
```

## Environment Configuration

```env
# Engines
ENABLE_CUA=1                           # Use OpenAI Computer Use (primary)
ENABLE_PLAYWRIGHT_FALLBACK=1           # Auto-fallback if CUA fails
ENABLE_PLAYWRIGHT=0                    # Force Playwright (debugging only)

# OpenAI
OPENAI_API_KEY=sk-...
CUA_MODEL=<your-computer-use-model>   # From your Models endpoint
CUA_TEMPERATURE=0.3
CUA_MAX_TOKENS=1200

# Decision Engine  
DECISION_MODE=hybrid                   # advisor|rubric|hybrid
OPENAI_DECISION_MODEL=<your-best-llm>  # For Advisor/Hybrid
THRESHOLD=0.72
ALPHA=0.50

# Runtime & Safety
YC_MATCH_URL=https://www.startupschool.org/cofounder-matching
PACE_MIN_SECONDS=45                    # Minimum seconds between sends
DAILY_QUOTA=25
WEEKLY_QUOTA=120
SHADOW_MODE=0                          # 1 = evaluate-only
```

## Events & Logging

### Schema (Canonical)
```json
// Decision event
{"event": "decision", "mode": "hybrid", "advisor_conf": 0.85, "rubric_score": 0.70, 
 "final_score": 0.775, "threshold": 0.72, "pass": true, "rationale": "Strong ML match"}

// Sent event (SUCCESS)
{"event": "sent", "ok": true, "mode": "auto", "verified": true, "chars": 312}

// Quota event
{"event": "quota", "day_count": 15, "week_count": 67, "allowed": true}

// Stop event  
{"event": "stop", "reason": "user_requested"}

// Model usage
{"event": "model_usage", "provider": "openai", "model": "<model>", 
 "tokens_in": 1200, "tokens_out": 150, "cost_est": 0.042}
```

### Logging Policy
- Use `LoggerPort` abstraction, never print() in business logic
- Log at boundaries (entry/exit of use cases)
- Include correlation IDs for request tracing
- Sensitive data (API keys) never logged

## Testing Strategy

### Test Pyramid
```
         /\
        /E2E\       ← Manual HIL only
       /━━━━\
      / INT  \      ← Headless, fixtures
     /━━━━━━━\
    / CONTRACT\     ← Port behavior
   /━━━━━━━━━━\
  /    UNIT    \    ← Pure logic, fast
 /━━━━━━━━━━━━━\
```

### Coverage Requirements
- Domain layer: ≥90% line coverage
- Application layer: ≥85% line coverage  
- Adapters: Contract tests required
- No test writes to $HOME (use tmp_path fixtures)

### Test Markers
```python
@pytest.mark.unit          # Fast, no IO
@pytest.mark.contract      # Port contract validation
@pytest.mark.integration   # May use Playwright (skipped if unavailable)
@pytest.mark.hil           # Requires manual setup
```

## Safety Invariants

### Never Send Without Verification
```python
# BAD
await browser.click_send()
logger.log({"event": "sent", "ok": true})

# GOOD
await browser.click_send()
if await browser.verify_sent():
    logger.log({"event": "sent", "ok": true, "verified": true})
else:
    logger.log({"event": "sent", "ok": false, "reason": "verification_failed"})
```

### STOP Flag Precedence
Before ANY action:
```python
if stop_controller.should_stop():
    logger.log({"event": "stop", "reason": "flag_detected"})
    return
```

### Quota Enforcement
```python
if not quota_port.check_allowed():
    logger.log({"event": "quota_exceeded"})
    return  # Never proceed
```

### Shadow Mode
```python
if config.shadow_mode:
    # Evaluate and log decision
    logger.log({"event": "decision", ...})
    # BUT NEVER SEND
    return
```

## Make Targets

```makefile
# Development
make doctor         # Check environment (must show repo-local paths)
make verify         # ruff + mypy + unit tests
make test-int       # Integration tests (headless)
make check-cua      # Verify OpenAI CUA availability

# Setup
make setup          # Install dependencies + browsers
make browsers       # Install Playwright browsers to .ms-playwright/

# Running
make run            # Start Streamlit UI (repo-scoped HOME)
make run-cli        # Show CLI options

# Maintenance  
make clean          # Remove caches and temp files
make clean-pyc      # Remove Python cache files
```

## Operations (Smallest Patch Rule)

### Model Upgrades
Change environment variable only:
```bash
# Before
CUA_MODEL=old-model

# After  
CUA_MODEL=new-model

# No code changes required
```

### Adding a Feature
1. Write failing test at appropriate level
2. Implement in correct layer (domain → application → infrastructure)
3. Wire in interface layer via DI
4. Update relevant documentation
5. Run `make verify` before committing

### Rollback Strategy
```bash
# Quick disable CUA (forces Playwright fallback)
export ENABLE_CUA=0
export ENABLE_PLAYWRIGHT=1

# Or use shadow mode to stop all sends
export SHADOW_MODE=1
```

## Code Review Checklist

- [ ] No hardcoded model names or API endpoints
- [ ] All environment variables documented in .env.example
- [ ] Tests pass without network access
- [ ] No writes to $HOME or system directories
- [ ] Ports used for external dependencies
- [ ] Error handling at adapter boundaries
- [ ] Events logged with correct schema
- [ ] Safety invariants preserved (STOP, quota, shadow)
- [ ] Documentation updated if behavior changed

## Common Pitfalls

### Notes on Agents Runner (optional)
If you use the Agents SDK Runner, the package is `openai-agents` but imports as `agents`. This project prefers the Responses API directly for the CUA loop; use the Runner only if it simplifies your integration.

### Hardcoded Models
```python
# WRONG
agent = Agent(model="computer-use-preview", ...)

# CORRECT
agent = Agent(model=os.getenv("CUA_MODEL"), ...)
```

### Mixing Layers
```python
# WRONG - domain importing infrastructure
# domain/services.py
from ..infrastructure.openai_cua_browser import OpenAICUABrowser

# CORRECT - domain defines interface, infrastructure implements
# domain/services.py
from ..application.ports import BrowserPort
```

### Synchronous Blocking
```python
# WRONG - blocks event loop
time.sleep(5)

# CORRECT - async sleep
await asyncio.sleep(5)
```

## Definition of Done

- [ ] Tests written and passing (appropriate level)
- [ ] Type hints on public interfaces
- [ ] No linting or type errors (`make verify` green)
- [ ] Documentation updated
- [ ] Events logged appropriately
- [ ] Runs with repo-scoped caches only
- [ ] PR reviewed by another engineer
- [ ] Deployed behind feature flag if risky

---

**Remember**: We're building an autonomous system that respects user control. Every line of code should support the pattern of **3 inputs → autonomous browsing → safe decisions → auditable actions**.
