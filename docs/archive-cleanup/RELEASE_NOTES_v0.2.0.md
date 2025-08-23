# Release v0.2.0 - Dynamic Model Resolution & Browser Improvements

## 🎉 Major Features

### Dynamic Model Resolution
- **Automatic model discovery** via OpenAI Models API - no more hardcoding!
- **Intelligent fallback chain**: GPT-5-thinking → GPT-5 → GPT-4
- **Account-aware**: Works across different OpenAI tier levels
- **Runtime configuration**: Models selected at startup based on availability

### Browser Automation Improvements
- ✅ **Single browser instance** - Fixed singleton pattern preventing multiple windows
- ✅ **Auto-login** - Automatic YC credential handling  
- ✅ **Profile detection** - Correctly identifies when on candidate pages
- ✅ **Session persistence** - Browser stays open across operations

### Message Generation
- ✅ **AI personalization** - Templates are personalized by GPT, not just pasted
- ✅ **Three-input flow** - Profile + Criteria + Template all sent to NLP
- ✅ **Decision modes** - Advisor, Rubric, and Hybrid modes working

## 🔧 Technical Improvements

### Architecture
- Implemented proper Responses API pattern for Computer Use
- AsyncLoopRunner singleton for browser management
- Clean separation of CUA (planner) and Playwright (executor)
- Full type safety with mypy strict mode

### Configuration
- Environment variables now optional (auto-discovery preferred)
- Better fallback handling when models unavailable
- Improved quota and rate limiting configuration

## 📊 What's Working

- ✅ Full autonomous browsing flow
- ✅ YC auto-login with stored credentials
- ✅ Profile navigation and evaluation
- ✅ AI-powered message generation
- ✅ Safety mechanisms (STOP flag, quotas, shadow mode)

## 🐛 Bug Fixes

- Fixed UnboundLocalError in Streamlit UI
- Fixed duplicate browser windows issue
- Fixed email field not being filled during login
- Fixed profile detection when landing on candidate pages
- Fixed quota blocking after single message

## 📚 Documentation

- Comprehensive README with architecture details
- Added AUDIT_AND_PLAN.md for implementation status
- Created MODEL_RESOLUTION_IMPLEMENTED.md
- Updated CLAUDE.md with latest patterns
- Added independent audit prompt for verification

## 🚀 Getting Started

```bash
# Install and configure
make setup
cp .env.example .env
# Add your OPENAI_API_KEY and YC credentials

# Run the app
make run
```

## ⚠️ Known Limitations

- Computer Use API requires Tier 3-5 OpenAI accounts
- GPT-5 not available on all accounts (falls back to GPT-4)
- YC may rate limit after extended use

## 🔄 Migration Guide

If upgrading from v0.1.x:
1. Remove hardcoded model names from .env (now auto-discovered)
2. Update SEND_DELAY_MS to PACE_MIN_SECONDS
3. Increase quotas (DAILY_QUOTA=100, WEEKLY_QUOTA=500)

## 🙏 Contributors

- JJ @ NovaMind NYC - Product vision and testing
- Claude AI Assistant - Implementation and refactoring
- External Auditor - Architecture validation

---

**For Hacker News**: This release demonstrates real-world usage of OpenAI's Computer Use API combined with GPT models for autonomous web automation. The dual-AI system (CUA for planning, GPT for decisions) showcases how to build sophisticated browser automation with proper safety controls.