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

## Step 3: Spawn Teammates

Use the **Task tool** to launch TWO teammates in **PARALLEL** (both in the same message):

**Strategist** (subagent_type: "the-council:strategist"):
```
GOAL: <the user's goal>

MEMORY (from past consultations):
<strategist-relevant portion of memory from Step 2>

Analyze this goal. 300-500 words. Start with your recommendation. Send your analysis back to the team lead via SendMessage when done.
```

**Critic** (subagent_type: "the-council:critic"):
```
GOAL: <the user's goal>

MEMORY (from past consultations):
<critic-relevant portion of memory from Step 2>

Critique this goal. 300-500 words. Start with the most critical issue. Every issue needs a fix. Send your analysis back to the team lead via SendMessage when done.
```

Wait for both to complete.

## Step 4: Synthesize

You received both analyses. Provide YOUR synthesis:
- Where they **agree** -> adopt
- Where they **conflict** -> YOU resolve with reasoning
- Where one raises something the other missed -> incorporate
- Be explicit about what you adopted from each

**One round only.** No re-consultation. No loops.

## Step 5: Record

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

## Step 6: Present

Present your synthesis to the user. Include:
1. The strategist's key recommendation
2. The critic's key concerns
3. Your decision and reasoning
4. Any lessons recorded
