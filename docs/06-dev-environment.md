# 06 — Developer Environment

**Status:** Draft v0.2 (2025-08-20)  
**Owner:** YC Matcher Team  
**Related:** [04-implementation-plan.md] · [05-operations-and-safety.md] · [07-project-structure.md]

## Baseline Requirements
- Python: 3.12+
- Package manager: `uv` (recommended) or `pip`
- Browser automation: Playwright (Chromium) — always used (executor)
- OpenAI API: Responses API with Computer Use tool; Agents SDK optional wrapper

## Core Dependencies

### Runtime
- `openai>=1.*`                 # OpenAI base SDK (Responses API)
- `playwright`                  # Browser control (executor)
- `openai-agents`               # Optional: Agents Runner wrapper (imports as `agents`)
- `streamlit`                   # Web UI dashboard
- `python-dotenv`               # Environment configuration
- `pydantic>=2.0.0`            # Data validation
- `sqlite3`                     # Built-in, for quotas and deduplication

### Import Surface (IMPORTANT)
Prefer Responses API directly for CUA; if you use Agents Runner, the package installs as `openai-agents` and imports as `agents`.

### Development
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `mypy` - Type checking
- `ruff` - Linting and formatting
- `pre-commit` - Git hooks

## Environment Variables

### Canonical Environment Configuration
```bash
# Engines
ENABLE_CUA=1                         # Use OpenAI Computer Use (primary)
ENABLE_PLAYWRIGHT_FALLBACK=1         # Auto-fallback if CUA fails
ENABLE_PLAYWRIGHT=0                  # Optional: force Playwright for debugging

# OpenAI
OPENAI_API_KEY=sk-...                # OpenAI API key
CUA_MODEL=<your-computer-use-model>  # Model id visible to your account
CUA_TEMPERATURE=0.3
CUA_MAX_TOKENS=1200

# Decision Engine
DECISION_MODE=advisor|rubric|hybrid
OPENAI_DECISION_MODEL=<your-best-llm>   # For Advisor/Hybrid reasoning
THRESHOLD=0.72
ALPHA=0.50                           # Hybrid weighting for Advisor

# Run-time & Safety
YC_MATCH_URL=https://www.startupschool.org/cofounder-matching
PACE_MIN_SECONDS=45                  # Minimum seconds between sends
DAILY_QUOTA=25
WEEKLY_QUOTA=120
SHADOW_MODE=0                        # 1 = evaluate-only (never send)

# Repo-scoped Caches (no $HOME writes)
UV_LINK_MODE=copy
UV_CACHE_DIR=.uv_cache
XDG_CACHE_HOME=.cache
PLAYWRIGHT_BROWSERS_PATH=.ms-playwright
MPLCONFIGDIR=.mplconfig
```

## Repo-Scoped Caches (No $HOME)

Ensure these are exported by your Makefile and visible in `make doctor`:

```bash
UV_CACHE_DIR=.uv_cache
XDG_CACHE_HOME=.cache
PLAYWRIGHT_BROWSERS_PATH=.ms-playwright
MPLCONFIGDIR=.mplconfig
UV_LINK_MODE=copy
```

### Streamlit Without Touching Real $HOME
To prevent Streamlit from writing `~/.streamlit`, run with a repo-scoped HOME:
```bash
mkdir -p .home
HOME="$PWD/.home" \
  uv run streamlit run -m yc_matcher.interface.web.ui_streamlit --server.port 8502
```

## Local Setup

### Initial Setup
```bash
# 1. Clone repository
git clone <repo-url>
cd yc-cofounder-bot

# 2. Install dependencies with uv
uv sync --all-extras

# 3. Install Playwright browsers (for fallback)
make browsers

# 4. Set up pre-commit hooks
uv run pre-commit install

# 5. Create .env file
cp .env.example .env
# Edit .env with your API keys and models

# 6. Create necessary directories
mkdir -p .uv_cache .cache .ms-playwright .mplconfig .runs .home
```

### Quick CUA Check
Verify CUA model visibility without a full run:
```bash
uv run python - <<'PY'
import os
from openai import OpenAI
client = OpenAI()
model = os.getenv("CUA_MODEL")
print("CUA_MODEL=", model or "<unset>")
print("✓ OpenAI client initialized; ensure model supports computer_use and truncation='auto'")
PY
```

Or use the make target:
```bash
make check-cua
```

## Playwright Browsers Install

Run:
```bash
make browsers
```

If this fails due to egress, verify CDN reachability:
```bash
curl -I https://playwright.azureedge.net/ || true
```

**Offline fallback** (from a machine where install succeeded):
```bash
cd .ms-playwright && zip -r ../ms-playwright-cache.zip . && cd -
# Transfer zip to target machine
rm -rf .ms-playwright
unzip ms-playwright-cache.zip -d .ms-playwright
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
```

## WSL / Windows Notes

*Prefer moving repo to WSL ext4 for fewer exec quirks.*

If staying under `/mnt/c`, ensure ownership and execute bits:
```bash
sudo chown -R $USER:$USER .
chmod -R u+rwX .ms-playwright .uv_cache .cache .mplconfig .runs .home
```

For WSL ext4 filesystem (recommended):
```bash
# Use ext4 filesystem (faster than NTFS mount)
cd ~/projects  # Not /mnt/c/...

# Install system dependencies for Playwright
sudo apt-get update
sudo apt-get install -y libnss3 libatk-bridge2.0-0
```

## Makefile Targets

```bash
# Environment setup
make setup          # Install all dependencies and browsers
make doctor         # Check environment health (shows repo-local paths)

# Quality checks
make lint           # Run ruff linter
make lint-fix       # Auto-fix lints and format
make format         # Auto-format code with ruff
make type           # Run mypy type checking
make test           # Run pytest suite
make verify         # Run all checks (lint + type + test)

# Integration testing
make browsers       # Install/reinstall Playwright browsers
make check-cua      # Verify OpenAI CUA access
make test-int       # Run integration tests
PLAYWRIGHT_HEADLESS=1 make test-int  # Headless adapter tests

# Running the app
make run            # Start Streamlit dashboard
make run-cli        # Show CLI help

# Cleaning
make clean          # Remove cache and temp files
make clean-pyc      # Remove Python cache files
```

## Project Structure
```
yc-cofounder-bot/
├── .env.example              # Template for environment variables
├── .env                      # Your local configuration (git-ignored)
├── Makefile                  # Development commands
├── pyproject.toml           # Project metadata and tool configs
│
├── src/
│   └── yc_matcher/
│       ├── domain/          # Core business logic
│       │   └── entities.py  # Profile, Criteria, Decision
│       │
│       ├── application/     # Use cases
│       │   └── use_cases.py # Evaluate, send, audit
│       │
│       ├── infrastructure/  # External adapters
│       │   ├── openai_cua_browser.py  # PRIMARY: OpenAI CUA
│       │   ├── playwright_browser.py  # FALLBACK: Playwright
│       │   └── openai_decision.py     # Decision engine
│       │
│       └── interface/       # User interfaces
│           ├── web/         # Streamlit dashboard
│           │   └── ui_streamlit.py
│           └── cli/         # Command-line tools
│               └── check_cua.py
│
├── tests/                   # Test suite
├── docs/                    # Documentation
└── .runs/                   # Runtime data (git-ignored)
    ├── stop.flag           # Stop control file
    ├── events.jsonl        # Event log
    ├── seen.sqlite         # Deduplication DB
    └── quota.sqlite        # Quota tracking DB
```

## Verify Everything End-to-End

### 1. Prep (one time)
```bash
mkdir -p .uv_cache .cache .ms-playwright .mplconfig .runs .home
make doctor
```
Expect `make doctor` to print only repo-local paths (no `$HOME`).

### 2. Quality & Unit Tests
```bash
make verify
```
Should show: ruff=0, mypy=0, tests pass.

### 3. Adapter Validation (headless)
```bash
make browsers
PLAYWRIGHT_HEADLESS=1 make test-int
```

### 4. Headful HIL (CUA-first with Playwright fallback)
```bash
export ENABLE_CUA=1
export ENABLE_PLAYWRIGHT_FALLBACK=1
export YC_MATCH_URL="https://www.startupschool.org/cofounder-matching"
HOME="$PWD/.home" uv run streamlit run -m yc_matcher.interface.web.ui_streamlit --server.port 8502
```

Expected artifacts update:
- `events.jsonl` (includes `{"event":"sent","ok":true,"mode":"auto","verified":true,...}`)
- `.runs/seen.sqlite` (dedupe)
- `.runs/quota.sqlite` (daily/weekly)
- `.runs/stop.flag` (STOP control)

## IDE Configuration

### VS Code Settings (.vscode/settings.json)
```json
{
  "python.defaultInterpreter": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.analysis.typeCheckingMode": "strict"
}
```

### PyCharm Settings
- Set Python interpreter to `.venv/bin/python`
- Enable Ruff as external tool
- Configure pytest as test runner
- Set working directory to project root

## Troubleshooting

### CUA API Access Denied
- Verify you have tier 3-5 access for OpenAI Computer Use
- Check API key is correctly set in .env
- Run `make check-cua` to verify setup
- Check your Models endpoint for available models

### Playwright Browser Issues
```bash
# Reinstall browsers
make browsers

# Or manually
uv run python -m playwright install --force chromium

# Check browser health
uv run python -m playwright doctor
```

### Permission Errors (WSL)
```bash
# Fix permissions
chmod -R 755 .runs/
chmod 644 .env
chmod -R u+rwX .ms-playwright .uv_cache .cache
```

### Import Errors
```bash
# Ensure uv environment is active
which python  # Should show .venv/bin/python

# Reinstall dependencies
uv sync --all-extras --refresh
```

### Agents SDK Import Issues (Optional)
If using Agents Runner and `from agents import ...` fails:
```bash
# Verify package installed
uv pip list | grep openai-agents

# Reinstall if needed
uv pip install openai-agents --force-reinstall
```
