# The Council - Claude Code Plugin

A Claude Code plugin that spawns adversarial strategist + critic satellites for architecture decisions, risk analysis, and complex implementations.

Each satellite runs as an independent `claude -p` subprocess with its own full context window. They analyze the same goal from opposing perspectives — the strategist decomposes and plans, the critic finds gaps and failure modes. You (the hub) synthesize their analyses into a final decision.

## Features

- **One-Command Setup** - `/council-setup` installs everything automatically
- **Adversarial Consultation** - Two independent satellites (strategist + critic) with dedicated context windows
- **Full Research Capabilities** - Satellites can use WebFetch, WebSearch, Task, and all code tools
- **Persistent Memory** - Decisions, lessons, and role-specific learnings persist across sessions
- **Memory Compaction** - Curator subagent compacts memory without consuming main session context
- **Auditable File Bus** - All satellite outputs and logs saved to disk for review

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) v1.0.33+
- Claude Code Max plan (satellites spawn `claude -p` subprocesses)
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (installed automatically by `/council-setup`)

## Quick Start

### 1. Install the plugin

Inside Claude Code:

```
/plugin marketplace add MasterMind-SL/the-council-plugin
/plugin install the-council@the-council-plugin
```

### 2. Restart Claude Code

Close and reopen Claude Code. You can open it from **any directory** — the plugin loads globally once installed.

### 3. Install dependencies

```
/council-setup
```

This installs `uv` (if needed) and Python packages. When it finishes, **restart Claude Code again** so the MCP server can connect.

### 4. Initialize in your project

```
/council-init
```

This creates `.council/` in your project with memory, bus, and logs directories.

### 5. Start consulting

```
/council-consult Should we use PostgreSQL or MongoDB for our event sourcing system?
```

> **Note:** The MCP server won't connect until dependencies are installed. If skills seem broken, run `/council-setup` and restart.

## Installation Options

### Option 1: Marketplace (recommended)

See [Quick Start](#quick-start) above.

### Option 2: From source (for development)

```bash
# Clone the repository
git clone https://github.com/MasterMind-SL/the-council-plugin
cd the-council-plugin

# Install dependencies
uv sync

# Launch Claude Code with the plugin loaded
claude --plugin-dir .
```

### Option 3: Team marketplace

Add this to your project's `.claude/settings.json` so team members get prompted to install it:

```json
{
  "extraKnownMarketplaces": {
    "the-council-plugin": {
      "source": {
        "source": "github",
        "repo": "MasterMind-SL/the-council-plugin"
      }
    }
  },
  "enabledPlugins": {
    "the-council@the-council-plugin": true
  }
}
```

## Usage

Once loaded, you get 7 slash commands:

| Command | Description |
|---------|-------------|
| `/council-setup` | Install dependencies (uv, packages) |
| `/council-init` | Initialize `.council/` in the current project |
| `/council-consult <goal>` | Spawn strategist + critic for adversarial consultation |
| `/council-status` | View recent decisions, memory summary, and stats |
| `/council-maintain` | Check memory health and compact if needed |
| `/council-reset` | Clear session data (add `--all` to also clear memory) |
| `/council-export <session_id>` | Export a consultation as shareable markdown |

### Example workflow

```
> /council-init

Council initialized. Directories created:
- .council/memory/ (persistent)
- .council/bus/ (satellite outputs)
- .council/logs/ (ephemeral)

> /council-consult Should we migrate from REST to GraphQL for our mobile API?

Spawning strategist + critic...

### Strategist Analysis
Recommends GraphQL for mobile: reduces over-fetching, single endpoint,
type-safe schema. Phased migration: new endpoints in GraphQL, legacy REST...

### Critic Analysis
HARD NO on full migration. Caching is harder (no HTTP cache for POST).
Existing REST clients break. N+1 query problem. Recommends: GraphQL
gateway in front of existing REST, mobile-only...

### Hub Synthesis
Adopted critic's gateway approach with strategist's phased timeline...

> /council-status

Consultations: 1 | Lessons: 3 | Memory: healthy
```

## Agents

The plugin includes 3 agents:

| Agent | Role | How it runs |
|-------|------|-------------|
| `strategist` | Forward-thinking analysis — architecture, decomposition, trade-offs | `claude -p` subprocess (dedicated context window) |
| `critic` | Adversarial analysis — gaps, failure modes, scope creep, security | `claude -p` subprocess (dedicated context window) |
| `curator` | Memory compaction — deduplicates and prunes memory logs | Native subagent via Task tool (zero main-session context cost) |

## How It Works

```
Claude Code <--STDIO/JSON-RPC--> MCP Server (src/server.py)
                                      |
                                 asyncio subprocess
                                      |
                              ┌───────┴───────┐
                              |               |
                         claude -p        claude -p
                        (strategist)       (critic)
                              |               |
                         writes to        writes to
                    bus/satellites/    bus/satellites/
```

The plugin runs as an **MCP server** that communicates with Claude Code via STDIO. When you consult, the server spawns two parallel `claude -p` subprocesses — each with its own full context window, model selection, and tool access. Satellites write their analyses to the file bus, and the hub (your main session) synthesizes them.

Why `claude -p` instead of native subagents? Each satellite gets a **dedicated context window** for deep independent analysis. They can use WebFetch, WebSearch, Task (sub-research), and all code tools — auto-approved without permission prompts since they run non-interactively.

## Memory System

The Council uses a two-layer memory system:

| Layer | Purpose | Files |
|-------|---------|-------|
| **Append-only logs** | Full audit trail, never modified | `{role}-log.md`, `decisions.md`, `lessons.jsonl` |
| **Compacted active files** | Deduplicated context loaded into satellites | `{role}-active.md` |

After each consultation, the hub appends:
- Role-specific learnings to `strategist-log.md` / `critic-log.md`
- The decision record to `decisions.md`
- Reusable lessons to `lessons.jsonl`

When memory grows large, `/council-maintain` spawns the curator subagent to compact logs into concise active files — without consuming your main session's context.

## Configuration

Optional `.council/config.yaml` in your project:

```yaml
model:
  default: opus       # Satellite model (default: opus)
  fallback: sonnet    # Fallback model (default: sonnet)

limits:
  max_turns: 10       # Max turns per satellite (default: 10)
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Skills run but Claude tries wrong approaches | MCP server not connected — dependencies not installed | Run `/council-setup`, restart Claude Code |
| `tool_consult` fails with "claude executable not found" | `claude` not in PATH for subprocess | Ensure Claude Code CLI is installed globally |
| Satellites time out after 5 minutes | Complex goal + high max_turns | Simplify the goal or check satellite logs in `.council/logs/` |
| "Council not initialized" error | `.council/` directory doesn't exist | Run `/council-init` in your project |

## Development

```bash
# Install dependencies
uv sync

# Run MCP server standalone (STDIO)
uv run python -m src.server

# Verify tools register
uv run python -c "from src.server import mcp; print([t.name for t in mcp._tool_manager.list_tools()])"
```

## License

MIT
