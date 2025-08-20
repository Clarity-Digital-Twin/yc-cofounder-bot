Developer Environment

## Baseline Requirements
- Python: 3.12+
- Package manager: `uv` (recommended) or `pip`
- Browser automation: Playwright (Chromium) as fallback
- AI SDK: OpenAI Agents SDK for Computer Use

## Core Dependencies
### Runtime
- `openai-agents` - For OpenAI Computer Use tool
- `openai>=1.12.0` - OpenAI base SDK
- `pillow>=10.0.0` - Screenshot processing (if needed)
- `pyautogui>=0.9.54` - Screen capture (handled by Computer Use tool)
- `playwright` - Fallback browser automation
- `streamlit` - Web UI dashboard
- `python-dotenv` - Environment configuration
- `pydantic>=2.0.0` - Data validation
- `sqlite3` - Built-in, for quotas and deduplication

### Development
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `mypy` - Type checking
- `ruff` - Linting and formatting
- `pre-commit` - Git hooks

## Environment Variables

### Canonical Environment Configuration
```bash
# Core toggles
ENABLE_CUA=1
ENABLE_PLAYWRIGHT_FALLBACK=1
DECISION_MODE=hybrid           # advisor|rubric|hybrid
THRESHOLD=0.72                 # auto-send threshold
ALPHA=0.65                     # hybrid weight
STRICT_RULES=0                 # rubric strictness

# OpenAI (Computer Use + reasoning)
OPENAI_API_KEY=sk-...
CUA_MODEL=<your account's computer-use model>   # read from env, not hardcoded
DECISION_MODEL=<your best reasoning model>      # used by Advisor/Hybrid
CUA_TEMPERATURE=0.3
CUA_MAX_TOKENS=1000

# Repo-scoped caches (no $HOME)
UV_LINK_MODE=copy
UV_CACHE_DIR=.uv_cache
XDG_CACHE_HOME=.cache
PLAYWRIGHT_BROWSERS_PATH=.ms-playwright
MPLCONFIGDIR=.mplconfig

# Quotas and Limits
DAILY_LIMIT=20                  # Max sends per day
WEEKLY_LIMIT=60                 # Max sends per week
SEND_DELAY_MS=5000              # Delay between sends (ms)

# Target
YC_MATCH_URL=https://www.startupschool.org/cofounder-matching

# Optional Features
SHADOW_MODE=0                   # 1=evaluate only, no sends
HIL_REQUIRED=0                  # 1=force manual approval
```

### Development Settings
```bash
# Caching (repo-scoped to avoid conflicts)
UV_CACHE_DIR=.cache/uv
XDG_CACHE_HOME=.cache
PLAYWRIGHT_BROWSERS_PATH=.cache/browsers

# Debugging
LOG_LEVEL=INFO                  # DEBUG|INFO|WARNING|ERROR
SAVE_SCREENSHOTS=0               # 1=save all screenshots
```

## Local Setup

### Initial Setup
```bash
# 1. Clone repository
git clone <repo-url>
cd yc-cofounder-bot

# 2. Create virtual environment with uv
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 3. Install dependencies
uv pip install -r requirements.txt

# 4. Install Playwright browsers (for fallback)
python -m playwright install chromium

# 5. Set up pre-commit hooks
pre-commit install

# 6. Create .env file
cp .env.example .env
# Edit .env with your API keys
```

### WSL-Specific Setup
For Windows Subsystem for Linux users:
```bash
# Use ext4 filesystem (faster than NTFS mount)
cd ~/projects  # Not /mnt/c/...

# Set proper permissions
chmod 755 .
chmod 644 .env

# Install system dependencies
sudo apt-get update
sudo apt-get install -y libnss3 libatk-bridge2.0-0
```

## Makefile Targets

```makefile
# Environment setup
make setup          # Install all dependencies and browsers
make doctor         # Check environment health

# Quality checks
make lint           # Run ruff linter
make format         # Auto-format code with ruff
make typecheck      # Run mypy type checking
make test           # Run pytest suite
make verify         # Run all checks (lint + type + test)

# Browser testing
make check-cua      # Verify CUA API access
make test-browser   # Test Playwright fallback
make browsers       # Reinstall browser binaries

# Running the app
make run            # Start Streamlit dashboard
make run-shadow     # Start in Shadow Mode (no sends)
make run-advisor    # Start in Advisor Mode (safest)

# Development
make clean          # Remove cache and temp files
make reset          # Clear databases and logs
```

## Project Structure
```
yc-cofounder-bot/
├── .env.example              # Template for environment variables
├── .env                      # Your local configuration (git-ignored)
├── Makefile                  # Development commands
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project metadata and tool configs
│
├── src/
│   ├── domain/              # Core business logic
│   │   ├── entities/        # UserProfile, MatchCriteria, Decision
│   │   └── services/        # Matching logic
│   │
│   ├── application/         # Use cases
│   │   ├── decision/        # Advisor, Rubric, Hybrid modes
│   │   └── messaging/       # Template rendering
│   │
│   ├── infrastructure/      # External adapters
│   │   ├── cua/            # OpenAICUA adapter
│   │   ├── browser/        # Playwright fallback
│   │   └── storage/        # SQLite repos, JSONL logger
│   │
│   └── interface/           # User interfaces
│       ├── web/            # Streamlit dashboard
│       └── cli/            # Command-line interface
│
├── tests/                   # Test suite
├── docs/                    # Documentation
└── .runs/                   # Runtime data (git-ignored)
    ├── stop.flag           # Stop control file
    ├── events.jsonl        # Event log
    ├── seen.sqlite         # Deduplication DB
    └── quota.sqlite        # Quota tracking DB
```

## IDE Configuration

### VS Code Settings
```json
{
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

### Common Issues

**CUA API Access Denied**
- Verify you have tier 3-5 access for OpenAI Computer Use
- Check API key is correctly set in .env
- Ensure sufficient API credits

**Playwright Browser Issues**
```bash
# Reinstall browsers
python -m playwright install --force chromium

# Check browser health
python -m playwright doctor
```

**Permission Errors (WSL)**
```bash
# Fix permissions
chmod -R 755 .runs/
chmod 644 .env
```

**Import Errors**
```bash
# Ensure virtual environment is activated
which python  # Should show .venv/bin/python

# Reinstall dependencies
uv pip install -r requirements.txt --force-reinstall
```
