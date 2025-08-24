#!/usr/bin/env python3
"""Setup context7 MCP server for Claude Code in this project."""

import json
from pathlib import Path


def setup_context7_mcp():
    """Add context7 MCP server to Claude configuration."""

    # Path to Claude config
    config_path = Path.home() / ".claude.json"

    # Current project path
    project_path = "/mnt/c/Users/JJ/Desktop/Clarity-Digital-Twin/yc-cofounder-bot"

    # Read existing config
    with open(config_path) as f:
        config = json.load(f)

    # Ensure projects section exists
    if "projects" not in config:
        config["projects"] = {}

    # Ensure this project exists
    if project_path not in config["projects"]:
        config["projects"][project_path] = {
            "mcpServers": {},
            "enabledMcpjsonServers": [],
            "disabledMcpjsonServers": [],
            "hasTrustDialogAccepted": True,
            "ignorePatterns": [],
            "hasCompletedProjectOnboarding": True
        }

    # Add context7 MCP server
    config["projects"][project_path]["mcpServers"]["context7"] = {
        "command": "npx",
        "args": [
            "-y",
            "@upstash/context7-mcp"
        ]
    }

    # Optional: Add with API key for higher rate limits
    # To use with API key, uncomment and replace YOUR_API_KEY:
    # config["projects"][project_path]["mcpServers"]["context7"]["args"].extend([
    #     "--api-key",
    #     "YOUR_API_KEY"
    # ])

    # Write updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print("✅ Context7 MCP server configured successfully!")
    print(f"   Project: {project_path}")
    print("   Server: context7")
    print("\n📝 Usage:")
    print("   1. Restart Claude Code")
    print("   2. In your prompts, add 'use context7' to fetch up-to-date documentation")
    print("\n💡 Examples:")
    print("   - 'How do I use pytest fixtures? use context7'")
    print("   - 'Show me OpenAI's latest API for GPT-5. use context7'")
    print("   - 'Create a Playwright test with async/await. use context7'")
    print("\n🔑 Optional: Get an API key at https://context7.com/dashboard for higher rate limits")

if __name__ == "__main__":
    try:
        setup_context7_mcp()
    except Exception as e:
        print(f"❌ Error setting up context7 MCP: {e}")
        print("   Please check your ~/.claude.json file manually")
