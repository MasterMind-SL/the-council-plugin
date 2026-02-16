---
name: setup
description: Install The Council plugin dependencies. Run this after installing the plugin.
---

# Council Setup

## Step 1: Check uv
Run: `uv --version`
If not found, tell the user to install uv:
- macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

## Step 2: Install dependencies
Run: `uv sync --directory "${CLAUDE_PLUGIN_ROOT}"`

## Step 3: Verify MCP server can import
Run: `uv run --directory "${CLAUDE_PLUGIN_ROOT}" python -c "from mcp.server.fastmcp import FastMCP; print('MCP OK')"`

## Step 4: Done
Tell the user:
- "Council plugin installed. Restart Claude Code to connect the MCP server."
- "Then run `/council:init` in any project to set up consultation."
