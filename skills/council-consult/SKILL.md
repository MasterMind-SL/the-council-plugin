---
name: council-consult
description: Adversarial consultation with strategist + critic teammates.
---

# Council Consultation

You are the **Hub** — orchestrator and synthesizer. Follow this protocol exactly.

## Input

Goal: "$ARGUMENTS"

If no goal provided, ask the user what they want to consult on and stop.

## Step 1: Verify

Check if `.council/` exists in the current project directory. If not, tell the user: "Run `/council:init` first." and stop.

## Step 2: Load Memory

Call `council_memory_load` with:
- `project_dir`: current project root (absolute path)
- `goal`: "$ARGUMENTS"
- `max_tokens`: 4000

Save the returned memory text — you'll inject it into teammate prompts.

## Step 3: Create Team

Use `TeamCreate` to create a team:
- `team_name`: "council"
- `description`: "Council consultation: <short version of goal>"

## Step 4: Spawn Teammates

Use the **Task tool** to launch TWO teammates in **PARALLEL** (both in the same message). Both MUST include `team_name: "council"` and a `name` parameter:

**Strategist** — Task with `subagent_type: "the-council:strategist"`, `team_name: "council"`, `name: "strategist"`:
```
GOAL: <the user's goal>

MEMORY (from past consultations):
<strategist-relevant portion of memory from Step 2>

Analyze this goal. 300-500 words. Start with your recommendation.
When done, send your full analysis to "team-lead" via SendMessage.
```

**Critic** — Task with `subagent_type: "the-council:critic"`, `team_name: "council"`, `name: "critic"`:
```
GOAL: <the user's goal>

MEMORY (from past consultations):
<critic-relevant portion of memory from Step 2>

Critique this goal. 300-500 words. Start with the most critical issue. Every issue needs a fix.
When done, send your full analysis to "team-lead" via SendMessage.
```

Wait for both teammates to send their analyses back.

## Step 5: Synthesize

You received both analyses via SendMessage. Provide YOUR synthesis:
- Where they **agree** -> adopt
- Where they **conflict** -> YOU resolve with reasoning
- Where one raises something the other missed -> incorporate
- Be explicit about what you adopted from each

**One round only.** No re-consultation. No loops.

## Step 6: Record

Call `council_memory_record` with:
- `project_dir`: same as Step 2
- `goal`: the original goal
- `strategist_summary`: 1-2 sentence summary of strategist's position
- `critic_summary`: 1-2 sentence summary of critic's position
- `decision`: your hub decision and reasoning (1-3 sentences)
- `strategist_lesson`: (optional) reusable insight from strategist
- `critic_lesson`: (optional) reusable insight from critic
- `hub_lesson`: (optional) meta-lesson from the synthesis
- `importance`: 1-10 based on decision significance
- `pin`: true only for critical, project-wide decisions

## Step 7: Cleanup

Shut down both teammates and delete the team:
1. `SendMessage` with `type: "shutdown_request"` to `"strategist"`
2. `SendMessage` with `type: "shutdown_request"` to `"critic"`
3. `TeamDelete` to remove the team

## Step 8: Present

Present your synthesis to the user. Include:
1. The strategist's key recommendation
2. The critic's key concerns
3. Your decision and reasoning
4. Any lessons recorded
