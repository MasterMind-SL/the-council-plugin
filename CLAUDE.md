# The Council — Plugin Runtime Instructions

## How It Works

This plugin provides **memory-only MCP tools** (`council_memory_*`) and **skills** (`/council:*`). Consultation orchestration happens via native agent teams — the skill spawns teammates (default: strategist-alpha + strategist-beta + critic, or custom roles), you synthesize as team-lead.

The plugin works from **any directory**. Skills and tools are available globally once loaded.

## Team Lead Protocol

After `/council:consult`, you are the **team-lead**. The skill handles spawning teammates and loading memory.

### Mode Routing

Before spawning teammates, analyze the goal and select a mode automatically:

| Mode | Triggers | Behavior |
|------|----------|----------|
| **default** | General consultations (no special triggers) | Standard: analyze, synthesize, record |
| **debate** | "debate", "vs", "compare", "which is better", "pros and cons", "trade-offs between" | Adds 1 rebuttal round: forward analyses to others, collect revised positions, then synthesize. ~2-3x token cost |
| **plan** | "plan", "roadmap", "PRD", "spec", "design", "architect", "implementation plan" | Same as default but synthesis output is numbered actionable steps with dependencies and priorities (P0/P1/P2) |
| **reflect** | "review our decisions", "what should we focus on", "gaps in our approach", "retrospective" | Loads memory + status before spawning. Teammates analyze decision history. Synthesis outputs prioritized future consultation recommendations |

### Custom Roles

Users can append `ROLES: role1, role2, ...` to the goal. When present:
- Extract and remove the ROLES clause from the goal before processing
- Spawn one teammate per role (max 5). Roles with "critic" or "auditor" use adversarial prompts, others use strategist prompts
- If no adversarial role is listed, auto-add "critic"
- When no ROLES clause: default 3-member council (strategist-alpha, strategist-beta, critic)
- Available curated roles: `architect`, `security-auditor`, `ux-reviewer`, `planner`

### Synthesis Rules

1. Synthesize: for each teammate's analysis — agreements -> adopt, divergences -> YOU pick, adversarial flags -> incorporate fix
2. Be explicit about what you adopted from each teammate
3. **One round only** for team-lead synthesis. Debate mode allows 1 rebuttal round among teammates.
4. Record results via `council_memory_record` (non-adversarial summaries -> `strategist_summary`, adversarial summaries -> `critic_summary`)

## MCP Tools (6)

| Tool | Purpose |
|------|---------|
| `council_memory_init` | Create `.council/` in a project |
| `council_memory_load` | Load goal-filtered, budget-aware memory (includes archive excerpts) |
| `council_memory_record` | Record consultation results to all tiers + grow topic keywords |
| `council_memory_status` | Show state + compaction recommendations |
| `council_memory_reset` | Clear data (optional: full with memory) |
| `council_memory_compact` | Write compacted entries (curator use) |

## Memory Features

- **Dynamic Topics**: Keywords grow from consultations. New topics emerge automatically.
- **Archive Discoverability**: Past lessons surface automatically when relevant to the current goal.
- **Budget-Aware**: Retrieval never exceeds token budget regardless of consultation count.

## When NOT to Consult

Most tasks do NOT need consultation. Only consult for: architecture decisions, complex implementations, risk analysis, security audits.

## Setup Issues

If MCP tools are unavailable, tell the user to run `/council:setup` then restart Claude Code.
