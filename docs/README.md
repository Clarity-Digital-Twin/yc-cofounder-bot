# YC Co-Founder Bot Documentation

## Quick Links

### 🚀 Getting Started
- [Project Status & Quick Start](technical/PROJECT_STATUS.md) - Current state and how to run
- [Development Environment](development/06-dev-environment.md) - Setup instructions

### 📖 Core Documentation
- [Product Brief](core/01-product-brief.md) - What this bot does
- [Architecture](core/03-architecture.md) - System design
- [Operations & Safety](core/05-operations-and-safety.md) - Safety mechanisms

### 🔧 Technical Reference
- [OpenAI API Guide](technical/OPENAI_API_GUIDE.md) - API usage patterns
- [YC UI Structure](technical/YC_UI_STRUCTURE.md) - Browser automation details
- [Event Schema](technical/event_schema.md) - Logging format

### 💻 Development
- [Project Structure](development/07-project-structure.md) - Code organization
- [Engineering Guidelines](development/11-engineering-guidelines.md) - Clean code practices
- [Testing & Quality](development/08-testing-quality.md) - Test strategy

## Project Overview

A bot that automates finding co-founders on YC's Startup School platform by:

1. **Browsing** profiles automatically using Playwright
2. **Evaluating** matches with GPT-4 AI
3. **Messaging** high-quality candidates

## Current Status (September 2025)

✅ **Core functionality working** - Browser automation, AI evaluation, and messaging all functional

⚙️ **Configuration needed** - Set YC credentials and OpenAI API key in `.env`

📋 **One known fix applied** - Removed unsupported `response_format` parameter for GPT-4

## File Organization

```
docs/
├── README.md              # This file
├── core/                  # Product & design docs
├── technical/             # Implementation details
├── development/           # Dev setup & guidelines
└── archive/              # Historical/outdated docs
```

## Primary References

- **CLAUDE.md** (root) - AI assistant instructions
- **README.md** (root) - Project overview
- **.env.example** - Configuration template