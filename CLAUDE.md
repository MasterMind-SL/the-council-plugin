# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Plugin Runtime Instructions

**IMPORTANT: Follow these instructions when the plugin is loaded and the user invokes any skill or asks about council consultations.**

### How this plugin works

This plugin provides MCP tools (prefixed `mcp__the-council__*` or shown as `tool_*` in skills). ALL consultation, memory management, and state operations go through these MCP tools. Do NOT try to manually spawn `claude -p` subprocesses, read memory files directly for decision-making, or modify `.council/` structure outside of the tools.

The plugin works from **any directory**. The user does NOT need to be inside the plugin folder. Skills and tools are available globally once the plugin is loaded.

### Detecting setup problems

When any skill is invoked, check if MCP tools are available:
- **If the MCP tools are available** (you can see `mcp__the-council__*` in your tool list): the plugin is properly installed and the MCP server is running. Proceed with the skill.
- **If the MCP tools are NOT available** (tool calls fail or tools don't appear): the MCP server failed to start. This almost always means dependencies aren't installed yet. Tell the user:

```
The Council plugin's MCP server is not connected. This usually means
dependencies haven't been installed yet.

Run this to set everything up:
  /council-setup

After it finishes, restart Claude Code for the MCP server to connect.
```

Do NOT attempt workarounds like spawning `claude -p` manually or reading memory files directly. The correct fix is always: install dependencies → restart Claude Code.

### Hub Protocol

You (Claude in the main session) are the **Hub** — orchestrator and synthesizer. After `tool_consult` returns both satellite analyses:

1. Present both analyses to the user
2. Synthesize:
   - Where satellites **agree** → adopt
   - Where they **conflict** → YOU resolve with reasoning
   - Where one raises something the other missed → incorporate
3. Be explicit about what you adopted from each satellite
4. **One round only.** No re-consultation. No loops.
5. Call `tool_record` with your decision

### When NOT to consult

Simple tasks — answer directly. Most tasks do NOT need satellites.
Only consult for: architecture decisions, complex implementations, risk analysis, security audits.

### Available MCP tools

| Tool | Purpose |
|------|---------|
| `tool_init` | Initialize `.council/` in a project directory |
| `tool_consult` | Spawn strategist + critic satellites in parallel |
| `tool_record` | Record consultation results to memory files |
| `tool_status` | Show council state — decisions, memory, feed, stats |
| `tool_reset` | Clear session data (optional: full reset with memory) |
| `tool_maintain` | Check memory health and line counts |
| `tool_export` | Export a consultation session as shareable markdown |

### Memory compaction

When `/council-maintain` indicates compaction is needed, use the **Task tool** to launch the `curator` subagent (defined in `agents/curator.md`). The curator runs in its own context window — zero cost to the main session. Do NOT compact memory manually in the main session.

---

## What This Is

A **Claude Code Plugin** that provides adversarial consultation via strategist + critic satellites. It bundles an MCP server, 7 skills (slash commands), and 3 agents.

## Architecture

```
Claude Code ←STDIO/JSON-RPC→ MCP Server (src/server.py)
                                   │
                              asyncio subprocess
                                   │
                            ┌──────┴──────┐
                            │             │
                       claude -p      claude -p
                      (strategist)     (critic)
                            │             │
                       writes to      writes to
                  bus/satellites/  bus/satellites/
```

The **MCP Server** (`src/server.py`) handles all state management and satellite spawning. When `tool_consult` is called, it launches two parallel `claude -p` subprocesses via `satellite.py`. Each satellite gets:

- Its agent definition as system prompt (`agents/{role}.md`)
- Persistent memory (active file or log file)
- Output instructions (where to write the analysis)
- Full tool access: `Read,Write,Glob,Grep,Bash,WebFetch,WebSearch,Task` (auto-approved via `--allowedTools`)
- Model selection from config (default: Opus with Sonnet fallback)

Satellites write their analysis to `.council/bus/satellites/{session_id}-{role}.md`. The MCP tool reads these files and returns both analyses to the main session for hub synthesis.

All stdout is reserved for MCP JSON-RPC; use stderr for logging.

## Loading the Plugin

The plugin must be explicitly loaded. Just being in the directory is NOT enough.

```bash
# Development mode (loads for current session only)
claude --plugin-dir /path/to/the-council-plugin
```

Once loaded, skills are available as `/council-consult`, `/council-init`, etc.

### Installing from marketplace (for end users)

Inside Claude Code:

```
/plugin marketplace add MasterMind-SL/the-council-plugin
/plugin install the-council@the-council-plugin
```

Then restart Claude Code and run `/council-setup` to install dependencies automatically.

Or install from a local clone:

```bash
git clone https://github.com/MasterMind-SL/the-council-plugin
cd the-council-plugin
uv sync
claude --plugin-dir .
```

### Plugin structure

```
the-council-plugin/
├── .claude-plugin/
│   ├── plugin.json          ← manifest (name, version, license)
│   └── marketplace.json     ← marketplace distribution config
├── .mcp.json                ← MCP server config (uv run python -m src.server)
├── skills/                  ← 7 skills (SKILL.md each)
│   ├── council-setup/
│   ├── council-consult/
│   ├── council-init/
│   ├── council-status/
│   ├── council-maintain/
│   ├── council-reset/
│   └── council-export/
├── agents/                  ← 3 agents
│   ├── strategist.md        ← satellite: forward-thinking analysis
│   ├── critic.md            ← satellite: adversarial analysis
│   └── curator.md           ← subagent: memory compaction
├── src/                     ← Python source (MCP server)
│   ├── __init__.py
│   ├── __main__.py          ← entry point (python -m src.server)
│   ├── server.py            ← FastMCP with 7 @mcp.tool() functions
│   ├── satellite.py         ← claude -p subprocess spawning
│   └── config.py            ← configuration with yaml override
├── .gitignore
├── CLAUDE.md
├── README.md
├── pyproject.toml
└── uv.lock
```

Components live at the plugin root, NOT inside `.claude-plugin/`. Only `plugin.json` and `marketplace.json` go there.

## Key Modules

| Module | Purpose |
|--------|---------|
| `src/server.py` | MCP entry point. Registers 7 `@mcp.tool()` functions. Handles init, consult, record, status, reset, maintain, export. |
| `src/satellite.py` | Spawns `claude -p` subprocesses. Builds system prompt (agent def + memory + output instructions), manages temp files, captures logs. `spawn_both()` runs strategist + critic in parallel via `asyncio.gather`. |
| `src/config.py` | Configuration with defaults (Opus model, Sonnet fallback, 10 max turns). Optional `.council/config.yaml` override per project. |

## Plugin Components

- **`.claude-plugin/plugin.json`**: Plugin manifest (name: `the-council`)
- **`.claude-plugin/marketplace.json`**: Marketplace config for `/plugin marketplace add` distribution
- **`.mcp.json`**: MCP server config. Uses `uv run --directory ${CLAUDE_PLUGIN_ROOT}` for cross-platform compatibility
- **`skills/`**: 7 skills — `council-setup`, `council-consult`, `council-init`, `council-status`, `council-maintain`, `council-reset`, `council-export`
- **`agents/`**: 2 satellite prompt sources (`strategist.md`, `critic.md`) + 1 native subagent (`curator.md`)

## Memory System

Two-layer memory per satellite role:

| Layer | File | Purpose |
|-------|------|---------|
| Append-only log | `{role}-log.md` | Full session history. Never modified. Audit trail. |
| Compacted active | `{role}-active.md` | Deduplicated, pruned. Loaded into satellite context. |

Shared memory:
- `decisions.md` — Hub decision record (date, goal, positions, decision). Never modified by satellites.
- `lessons.jsonl` — Structured lessons `{"ts", "lesson", "source"}`. Append-only.
- `bus/feed.jsonl` — Event feed for dashboard/debugging.

### Compaction

When memory grows large (log > 150 lines or log > 80 lines with no active file), `tool_maintain` recommends compaction. The `/council-maintain` skill then spawns the **curator** subagent via Task tool. The curator:

1. Reads both role logs, decisions.md, and lessons.jsonl
2. Identifies duplicates, superseded entries, and mergeable insights
3. Writes compacted `{role}-active.md` (target: under 150 lines)
4. NEVER modifies logs or decisions — only writes active files

The curator runs in its own context window. Zero cost to the main session.

## Satellite Spawning Details

Each satellite is a `claude -p` subprocess with these flags:

```
claude -p
  --model opus
  --fallback-model sonnet
  --append-system-prompt-file <temp-system-prompt>
  --allowedTools Read,Write,Glob,Grep,Bash,WebFetch,WebSearch,Task
  --max-turns 10
  --no-session-persistence
  --output-format stream-json
```

Key design decisions:
- **`--append-system-prompt-file`**: Agent definition + memory + output instructions go in the system prompt. The goal goes as stdin (user message). This separates identity from task.
- **`--allowedTools`**: Auto-approves all listed tools without permission prompts. Required because `claude -p` is non-interactive — no way to prompt the user. Designed for Max accounts.
- **`--no-session-persistence`**: Satellites don't persist in `claude --resume` list. Ephemeral by design.
- **`CLAUDECODE` env removed**: Prevents subprocess detection issues when spawning `claude -p` from within a Claude Code session.
- **5-minute timeout**: Prevents runaway satellites. Check `.council/logs/` if a satellite times out.

## .council/ Directory Structure

Created by `tool_init` in the user's project:

```
{project}/
└── .council/
    ├── memory/
    │   ├── strategist-log.md       ← append-only role history
    │   ├── strategist-active.md    ← compacted active memory
    │   ├── critic-log.md
    │   ├── critic-active.md
    │   ├── decisions.md            ← hub decision record
    │   └── lessons.jsonl           ← structured lessons
    ├── bus/
    │   ├── satellites/             ← satellite output files (gitignored)
    │   └── feed.jsonl              ← event feed (gitignored)
    ├── logs/                       ← satellite stdout logs (gitignored)
    └── .tmp/                       ← temp system prompt files (gitignored)
```

Gitignored: `bus/satellites/`, `logs/`, `.tmp/`. Persistent: everything in `memory/`.

## Configuration

Optional `.council/config.yaml`:

```yaml
model:
  default: opus       # Satellite model
  fallback: sonnet    # Fallback if primary unavailable

limits:
  max_turns: 10       # Max agentic turns per satellite
```

If no config file exists, defaults are used (Opus, Sonnet fallback, 10 turns).

## Development

```bash
# Install dependencies
uv sync

# Run MCP server standalone (STDIO)
uv run python -m src.server

# Verify tools register
uv run python -c "from src.server import mcp; print([t.name for t in mcp._tool_manager.list_tools()])"

# Test MCP protocol handshake
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | uv run python -m src.server
```
