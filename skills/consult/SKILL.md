---
name: consult
description: Spawn strategist + critic satellites for adversarial consultation. Use for architecture decisions, complex implementations, risk analysis, or security audits.
---

# Council Consultation

You are the **Hub** — orchestrator and synthesizer.

## Step 1: Call tool_consult

Call `tool_consult` with:
- `goal`: "$ARGUMENTS" (the user's consultation goal)
- `project_dir`: The current project root directory (absolute path)

If no goal provided, ask the user what they want to consult on and stop.
If the tool returns "not initialized", tell the user to run `/council:init` first.

## Step 2: Synthesize

The tool returns both satellite analyses. You are the Hub. Provide YOUR synthesis:
- Where satellites **agree** → adopt
- Where they **conflict** → YOU resolve with reasoning
- Where one raises something the other missed → incorporate
- Be explicit about what you adopted from each

**One round only.** Do not re-consult. Do not loop.

## Step 3: Record

Call `tool_record` with:
- `project_dir`: same as Step 1
- `session_id`: from the tool_consult response
- `goal`: the original goal
- `strategist_summary`: 1-2 sentence summary of strategist's position
- `critic_summary`: 1-2 sentence summary of critic's position
- `decision`: your hub decision and reasoning
- `strategist_lesson`: (optional) reusable insight from strategist
- `critic_lesson`: (optional) reusable insight from critic
- `hub_lesson`: (optional) meta-lesson from the synthesis
