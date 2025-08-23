# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YC Co-Founder Matching Bot - Autonomous browser automation for YC/Startup School cofounder matching using OpenAI GPT-5/GPT-4 + Playwright.

The system takes 3 inputs (Your Profile, Match Criteria, Message Template) and autonomously browses YC Cofounder Matching, evaluates profiles using AI (GPT-5 when available, GPT-4 fallback), and sends messages when match quality exceeds threshold.

⚠️ **IMPORTANT GPT-5 FACTS (August 2025)**:
- GPT-5 model ID is `gpt-5` (NOT `gpt-5-thinking`)
- GPT-5 uses Responses API (NOT Chat Completions)
- Not all API keys have GPT-5 access - check with `client.models.list()`
- See GPT5_FACTS.md for complete details

## Development Philosophy - Clean Code Principles

This codebase honors Uncle Bob's Clean Code principles. When contributing:

### Core Principles (Non-Negotiable)
- **SOLID**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **DRY**: Don't Repeat Yourself - extract common patterns into reusable components
- **GoF Patterns**: Use established design patterns (Strategy for decisions, Adapter for browsers, Repository for persistence)
- **TDD**: Write tests FIRST, then implementation. Red → Green → Refactor cycle
- **DDD**: Domain logic stays pure in `domain/`, infrastructure concerns in `infrastructure/`
- **Type Safety**: Full type hints on ALL functions. Run `make type` before EVERY commit
- **Linting**: Code must pass `make verify` (ruff + mypy + tests) before pushing

### Development Workflow
1. Write failing test that describes the behavior
2. Implement minimal code to make test pass
3. Refactor to clean, following SOLID principles
4. Ensure full type coverage (`mypy --strict`)
5. Run `make verify` - must be green
6. Commit with descriptive message

### Code Quality Standards
```python
# ✅ GOOD - Clean, typed, single responsibility
async def calculate_rubric_score(
    profile: ProfileData,
    criteria: MatchCriteria,
    weights: RubricWeights
) -> float:
    """Calculate deterministic rubric score for profile match."""
    score = 0.0
    score += weights.skills * _calculate_skill_overlap(profile.skills, criteria.required_skills)
    score += weights.location * _calculate_location_match(profile.location, criteria.locations)
    return min(1.0, score)

# ❌ BAD - Mixed concerns, no types, doing too much
def process(data):
    # Parse profile
    # Calculate score
    # Make decision
    # Send message
    # Log to database
    return result
```

## Essential Commands

```bash
# Setup & Installation
make setup          # Install deps + browsers + pre-commit hooks
make browsers       # Install Playwright Chromium (repo-local)
make doctor         # Verify repo-scoped caches (no $HOME writes)

# Development
make lint           # Run ruff lints
make lint-fix       # Auto-fix lints and format
make format         # Apply ruff formatting
make type           # Run mypy type checking

# Testing
make test           # Run unit tests only
make test-int       # Run integration tests (requires PLAYWRIGHT_HEADLESS=1)
make verify         # Run lint + type + tests (CI equivalent)
pytest tests/unit/test_specific.py::TestClass::test_method  # Run single test

# Running the Application
make run            # Launch Streamlit UI (primary interface)
make run-cli        # CLI runner (optional)
make check-cua      # Verify OpenAI CUA model access

# Cleanup
make clean          # Remove build artifacts
make clean-pyc      # Remove Python cache files
```

## Critical Architecture Understanding

### CUA + Playwright Relationship (MOST IMPORTANT)
**CUA and Playwright work TOGETHER, not as alternatives:**
- CUA (via OpenAI Responses API) = **Planner/Analyzer** - analyzes screenshots, suggests actions
- Playwright = **Executor** - controls browser, takes screenshots, executes actions
- The Loop: Playwright screenshot → CUA analyze → CUA suggest → Playwright execute → repeat
- Fallback Mode: When CUA unavailable, use Playwright-only with hardcoded selectors

### Domain-Driven Design Layers (Hexagonal Architecture)
```
src/yc_matcher/
├── domain/          # Pure business logic (ports/contracts) - NO external dependencies
│   ├── ports/       # Interfaces: ComputerUsePort, DecisionPort, QuotaPort, etc.
│   └── models/      # Domain entities: Candidate, Criteria, DecisionResult
├── application/     # Use cases orchestrating domain logic (depends only on domain)
│   └── use_cases.py # ProcessCandidateUseCase (the main flow)
├── infrastructure/  # External adapters/implementations (implements domain ports)
│   ├── openai_cua_browser.py     # CUA via Responses API + Playwright (PRIMARY)
│   ├── browser_playwright.py      # Playwright-only fallback
│   ├── openai_decision_adapter.py # LLM decision making
│   └── sqlite_*.py                # Repository pattern implementations
└── interface/       # Entry points (wires everything via DI)
    ├── web/ui_streamlit.py  # Streamlit dashboard (3-input UI)
    └── di.py                # Dependency injection wiring
```

**Key DDD Rules:**
- Domain layer has ZERO dependencies on infrastructure
- All external concerns go through ports (interfaces)
- Use cases orchestrate but don't implement business logic
- Infrastructure adapters are swappable (Liskov Substitution)

### Decision Modes (3 Interchangeable)
1. **Advisor**: LLM-only evaluation, requires manual approval
2. **Rubric**: Deterministic scoring based on weights, auto-sends if threshold met
3. **Hybrid**: Combines LLM confidence + rubric score (α-weighted), auto-sends if threshold met

### Event-Driven Logging
Every action emits JSONL events to `.runs/events.jsonl`:
- `decision`: Mode, scores, rationale, extracted fields
- `sent`: Profile ID, success status, verification
- `stopped`: Reason for stopping
- `model_usage`: Token counts and cost estimates

## Environment Configuration

Required in `.env` (copy from `.env.example`):
```bash
# Critical
OPENAI_API_KEY=sk-...
CUA_MODEL=<from your Models endpoint>      # e.g., "computer-use-preview"
OPENAI_DECISION_MODEL=gpt-5                # Use gpt-5 (NOT gpt-5-thinking!)

# Decision Configuration
DECISION_MODE=ai                           # AI-only mode (simplified)
THRESHOLD=0.72                             # Auto-send threshold
ALPHA=0.50                                 # Hybrid weight (0=all rubric, 1=all LLM)

# Safety & Limits
PACE_MIN_SECONDS=45                        # Between sends (NOT SEND_DELAY_MS!)
DAILY_QUOTA=25
WEEKLY_QUOTA=120
SHADOW_MODE=0                              # 1 = evaluate-only, never send

# Feature Flags
ENABLE_CUA=1                               # Use CUA as primary
ENABLE_PLAYWRIGHT_FALLBACK=1               # Fallback when CUA fails
```

## Current Status

The codebase is **95% complete** with recent fixes applied:

### Recently Fixed (December 2025)
1. **openai_cua_browser.py**: ✅ Migrated to Responses API with proper response parsing
2. **openai_decision.py**: ✅ Fixed GPT-5 response parsing to handle reasoning items
3. **check_cua.py**: ✅ Updated to verify access via Responses API (no Agents SDK)
4. **Response Parsing**: ✅ Now properly uses `output_text` helper and handles reasoning items

### Still Needs Work
1. **ui_streamlit.py**: Add 3-input mode behind feature flag (currently paste-based)
2. **di.py**: Wire decision mode selection
3. **use_cases.py**: Replace SEND_DELAY_MS with PACE_MIN_SECONDS

### OpenAI CUA Implementation Pattern (Correct)
```python
# The Responses API loop with Playwright executor:
resp = client.responses.create(
    model=os.getenv("CUA_MODEL"),
    input=[{"role": "user", "content": instruction}],
    tools=[{"type": "computer_use_preview", "display_width": 1280, "display_height": 800}],
    truncation="auto",
    previous_response_id=prev_id
)

if resp.computer_call:
    # Execute with Playwright
    await playwright_page.click(resp.computer_call.coordinates)
    
    # Send result back with screenshot
    screenshot = await playwright_page.screenshot()
    client.responses.create(
        previous_response_id=resp.id,
        computer_call_output={"call_id": resp.computer_call.id, "screenshot": b64(screenshot)},
        truncation="auto"
    )
```

## Testing Conventions (TDD Required)

### Test-Driven Development Process
1. **RED**: Write a failing test that describes desired behavior
2. **GREEN**: Write minimal code to make the test pass
3. **REFACTOR**: Clean up code while keeping tests green

### Test Structure
```python
# ✅ GOOD - Clear Arrange-Act-Assert with full typing
async def test_rubric_score_calculation() -> None:
    """Test that rubric scoring follows weighted calculation."""
    # Arrange
    profile = ProfileData(skills=["python", "ml"], location="SF")
    criteria = MatchCriteria(required_skills=["python"], locations=["SF"])
    weights = RubricWeights(skills=0.6, location=0.4)
    
    # Act
    score = await calculate_rubric_score(profile, criteria, weights)
    
    # Assert
    assert score == 1.0  # Perfect match
    assert isinstance(score, float)
```

### Testing Layers
- **Unit tests**: Pure domain logic, no I/O, fully deterministic
- **Integration tests**: Test adapters with mocked external services
- **Contract tests**: Verify ports/adapters honor interfaces
- **E2E tests**: Full flow with `PLAYWRIGHT_HEADLESS=1`

### Testing Rules
- Every public method needs a test
- Tests must be independent (no shared state)
- Use dependency injection for testability
- Mock at port boundaries, not random locations
- Test file mirrors source file: `src/module.py` → `tests/unit/test_module.py`

## Safety Mechanisms

1. **STOP flag**: `.runs/stop.flag` halts execution within 2 seconds
2. **Quotas**: SQLite-backed daily/weekly limits in `.runs/quota.sqlite`
3. **Deduplication**: Never message same profile twice (`.runs/seen.sqlite`)
4. **Shadow Mode**: Evaluate-only mode for testing without sending
5. **HIL approval**: Advisor mode requires manual approval before sending
6. **Pacing**: Enforced minimum delay between sends (PACE_MIN_SECONDS)

## Documentation Structure

- `/docs/*.md` - 12 comprehensive design documents
- Root-level `*REFACTOR*.md` - Implementation plans
- `CUA_PLAYWRIGHT_RELATIONSHIP.md` - Critical understanding of how components work together
- `MODEL_SELECTION.md` - Guide for choosing OpenAI models

## Common Issues & Solutions

1. **"Responses API not working"**: Check that your OpenAI SDK supports Responses API and CUA_MODEL is set correctly
2. **"SEND_DELAY_MS undefined"**: Use PACE_MIN_SECONDS instead (45 seconds minimum)
3. **Browser not launching**: Run `make browsers` to install Playwright locally
4. **CUA not working**: Check `make check-cua` and verify CUA_MODEL in your OpenAI account
5. **"model gpt-5-thinking not found"**: Use `gpt-5` instead (see GPT5_FACTS.md)
6. **"unsupported parameter: max_tokens"**: GPT-5 uses `max_output_tokens` with Responses API
7. **"Silent skips/no messages sent"**: Fixed - was due to incorrect parsing of GPT-5 reasoning items

## Key Invariants

- If STOP flag exists → abort before any send
- Never send if profile already in seen database
- Never exceed daily/weekly quotas
- Always log decision event before sent event
- CUA plans, Playwright executes (they work together, not as alternatives)

## Clean Code Patterns to Follow

### Design Patterns Used
- **Strategy Pattern**: Decision modes (Advisor/Rubric/Hybrid) are interchangeable strategies
- **Adapter Pattern**: Browser implementations (CUA/Playwright) adapt to common port
- **Repository Pattern**: Persistence (SQLite) hidden behind repository interfaces
- **Dependency Injection**: All dependencies wired through DI container
- **Factory Pattern**: Use factory methods for complex object creation

### Refactoring Checklist
Before committing any code:
- [ ] Single Responsibility: Each class/function does ONE thing
- [ ] Open/Closed: Extensible via interfaces, not modification
- [ ] Interface Segregation: Small, focused interfaces
- [ ] Dependency Inversion: Depend on abstractions (ports), not concretions
- [ ] DRY: No duplicated logic
- [ ] Type Safety: 100% type coverage, `mypy --strict` passes
- [ ] Test Coverage: All new code has tests written FIRST
- [ ] Clean Names: Descriptive, intention-revealing names
- [ ] Small Functions: <20 lines, single level of abstraction
- [ ] No Side Effects: Functions either command or query, not both

### Code Smells to Avoid
- God classes doing everything
- Primitive obsession (use domain types)
- Feature envy (methods using another class's data)
- Data clumps (group related parameters)
- Long parameter lists (>3 params = use object)
- Comments explaining bad code (refactor instead)
- Dead code (delete it)
- Speculative generality (YAGNI)