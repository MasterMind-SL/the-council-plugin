# The Council — Plugin Runtime Instructions

## How It Works

This plugin provides **memory-only MCP tools** (`council_memory_*`) and **skills** (`/council:*`). Consultation orchestration happens via native agent teams — the skill spawns strategist + critic as teammates, you synthesize as Hub.

The plugin works from **any directory**. Skills and tools are available globally once loaded.

## Hub Protocol

After `/council:consult`, you are the **Hub**. The skill handles spawning teammates and loading memory. Your job:
1. Synthesize: agree -> adopt, conflict -> YOU resolve, missed -> incorporate
2. Be explicit about what you adopted from each satellite
3. **One round only.** No re-consultation. No loops.
4. Record results via `council_memory_record`

## MCP Tools (6)

| Tool | Purpose |
|------|---------|
| `council_memory_init` | Create `.council/` in a project |
| `council_memory_load` | Load goal-filtered, budget-aware memory |
| `council_memory_record` | Record consultation results to all tiers |
| `council_memory_status` | Show state + compaction recommendations |
| `council_memory_reset` | Clear data (optional: full with memory) |
| `council_memory_compact` | Write compacted entries (curator use) |

## When NOT to Consult

Most tasks do NOT need consultation. Only consult for: architecture decisions, complex implementations, risk analysis, security audits.

## Setup Issues

If MCP tools are unavailable, tell the user to run `/council:setup` then restart Claude Code.
