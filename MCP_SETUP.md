# Context7 MCP Server Setup

This repository is configured with the **Context7 MCP (Model Context Protocol) server** for Claude Code, enabling access to up-to-date documentation and code examples directly in your prompts.

## ✅ Setup Complete

The context7 MCP server has been configured for this project at:
```
/mnt/c/Users/JJ/Desktop/Clarity-Digital-Twin/yc-cofounder-bot
```

## 📚 What is Context7?

Context7 is an MCP server that fetches real-time, version-specific documentation and code examples from official sources directly into Claude's context window. This ensures you get:

- **Up-to-date API references** - No outdated or hallucinated APIs
- **Version-specific documentation** - Accurate for the exact version you're using
- **Official code examples** - Straight from the source documentation
- **Zero context switching** - Documentation comes to you

## 🚀 How to Use

### Basic Usage

Simply add `use context7` to any prompt where you want current documentation:

```
"How do I set up OpenAI's GPT-5 with the Responses API? use context7"
```

### Examples for This Project

Since this is a YC Co-Founder Bot project, here are relevant examples:

1. **OpenAI API Documentation**
   ```
   "Show me the latest OpenAI GPT-5 API with response_format parameter. use context7"
   ```

2. **Playwright Testing**
   ```
   "How do I write async Playwright tests with proper page waiting? use context7"
   ```

3. **Pytest Fixtures**
   ```
   "Explain pytest fixtures with async support and show examples. use context7"
   ```

4. **Streamlit Components**
   ```
   "Show me how to create custom Streamlit components with state management. use context7"
   ```

5. **SQLite with Python**
   ```
   "How do I use SQLite with context managers in Python? use context7"
   ```

## 🔧 Configuration Details

The MCP server is configured in `~/.claude.json`:

```json
{
  "projects": {
    "/mnt/c/Users/JJ/Desktop/Clarity-Digital-Twin/yc-cofounder-bot": {
      "mcpServers": {
        "context7": {
          "command": "npx",
          "args": ["-y", "@upstash/context7-mcp"]
        }
      }
    }
  }
}
```

## 🔑 Optional: API Key for Higher Limits

While context7 works without an API key, you can get one for higher rate limits:

1. Visit https://context7.com/dashboard
2. Create an account and get your API key
3. Update the configuration:

```python
# Run this to add your API key:
uv run python setup_context7_mcp.py
# Then uncomment and update the API key section in the script
```

## 🔄 Restart Required

**Important**: After setup, you must restart Claude Code for the MCP server to be available.

## 🛠️ Troubleshooting

If context7 doesn't work:

1. **Check Node.js version**: Ensure Node.js 18+ is installed
   ```bash
   node --version
   ```

2. **Verify configuration**: Check that the config was added
   ```bash
   cat ~/.claude.json | grep context7
   ```

3. **Restart Claude Code**: Changes require a restart

4. **Test the connection**: Try a simple prompt
   ```
   "What is pytest? use context7"
   ```

## 📋 Benefits for This Project

Having context7 configured means:

- **Accurate OpenAI API usage** - Always get the latest GPT-5/GPT-4 API syntax
- **Current Playwright patterns** - No deprecated methods in browser automation
- **Modern Python practices** - Up-to-date async/await patterns
- **Latest testing approaches** - Current pytest and unittest documentation

## 🔗 Resources

- Context7 Dashboard: https://context7.com/dashboard
- MCP Documentation: https://modelcontextprotocol.io/
- Claude Code MCP Guide: https://docs.anthropic.com/en/docs/claude-code/mcp

---

*Setup completed on: August 24, 2025*