---
name: council-build
description: Full build pipeline — 3 council consultations (PRD, tech deck, backlog) followed by parallel implementation with dev teams.
---

# Council Build Pipeline

You are the **team-lead** — orchestrator across 4 phases. Follow this protocol exactly.

## Input

Goal: "$ARGUMENTS"

If no goal provided, ask the user what they want to build and stop.

## Step 0: Gate Check

### 0a. Verify initialization

Check if `.council/` exists in the current project directory. If not, tell the user: "Run `/council:init` first." and stop.

### 0b. Cost warning

Tell the user:

> **Build pipeline cost warning**
>
> This will run 3 sequential council consultations (9 agent spawns) followed by parallel implementation with 2+ dev teams. Estimated token cost: **50,000-150,000+ tokens** depending on project complexity.
>
> Phases:
> 1. PRD consultation (strategist-alpha, strategist-beta, critic)
> 2. Tech deck consultation (architect, strategist-alpha, security-auditor)
> 3. Backlog consultation (planner, strategist-beta, critic)
> 4. Parallel implementation (2+ dev teams from backlog)
>
> Continue? (y/n)

Wait for the user to confirm. If they decline, stop.

### 0c. Create artifacts directory

Create the directory `.council/build/` if it does not exist.

## Step 1: Load Memory

Call `council_memory_load` with:
- `project_dir`: current project root (absolute path)
- `goal`: "$ARGUMENTS"
- `max_tokens`: 4000

Save the returned memory text. It will be injected into all consultation phases.

---

## PHASE 1: PRD Consultation

> Roles: strategist-alpha, strategist-beta, critic (default council)

### 1.1 Create team

Use `TeamCreate`:
- `team_name`: "council-build-prd"
- `description`: "Build pipeline Phase 1: PRD for <short goal>"

### 1.2 Spawn teammates (all in PARALLEL)

Launch ALL 3 teammates in the same message via **Task tool**. All MUST include `team_name: "council-build-prd"` and a `name` parameter.

**Strategist Alpha** — `name: "strategist-alpha"`, `subagent_type: "the-council:strategist"`:
```
GOAL: $ARGUMENTS

CONTEXT: You are in Phase 1 of a build pipeline. Your task is to help create a Product Requirements Document (PRD).

MEMORY (from past consultations):
<memory from Step 1>

You are Strategist Alpha (ambitious, forward-thinking). Analyze this goal and propose PRD content. 400-600 words.
Cover: problem statement, target users, success metrics, core features (P0/P1/P2), user stories, scope boundaries, and non-functional requirements.
Push for the best possible product outcome.
When done, send your full analysis to "team-lead" via SendMessage.
```

**Strategist Beta** — `name: "strategist-beta"`, `subagent_type: "the-council:strategist"`:
```
GOAL: $ARGUMENTS

CONTEXT: You are in Phase 1 of a build pipeline. Your task is to help create a Product Requirements Document (PRD).

MEMORY (from past consultations):
<memory from Step 1>

You are Strategist Beta (pragmatic, conservative). Analyze this goal and propose PRD content. 400-600 words.
Cover: problem statement, target users, success metrics, core features (P0/P1/P2), user stories, scope boundaries, and non-functional requirements.
Focus on what is achievable, minimize risk and scope creep. Identify MVP boundaries.
When done, send your full analysis to "team-lead" via SendMessage.
```

**Critic** — `name: "critic"`, `subagent_type: "the-council:critic"`:
```
GOAL: $ARGUMENTS

CONTEXT: You are in Phase 1 of a build pipeline. Your task is to critique a Product Requirements Document (PRD).

MEMORY (from past consultations):
<memory from Step 1>

Critique this goal as a PRD. 400-600 words. Start with the most critical issue.
Focus on: missing requirements, ambiguous scope, conflicting user stories, unrealistic success metrics, hidden technical constraints, missing edge cases.
Every issue needs a specific fix. Prioritize by severity.
When done, send your full analysis to "team-lead" via SendMessage.
```

Wait for all 3 teammates to send their analyses.

### 1.3 Synthesize PRD

Apply standard synthesis rules:
- Where teammates **agree** → adopt immediately
- Where teammates **diverge** → evaluate which approach better fits the context
- Where the critic raises **valid concerns** → incorporate fixes
- Be explicit about what you adopted from each teammate

Format as a PRD with these sections:
1. **Problem Statement**
2. **Target Users**
3. **Success Metrics** (measurable)
4. **Core Features** (P0 = must-have, P1 = should-have, P2 = nice-to-have)
5. **User Stories** (As a..., I want..., So that...)
6. **Scope Boundaries** (in-scope vs out-of-scope)
7. **Non-Functional Requirements** (performance, security, accessibility)
8. **Assumptions & Constraints**

### 1.4 Write PRD artifact

Write the synthesized PRD to `.council/build/prd.md`.

### 1.5 Record Phase 1

Call `council_memory_record` with:
- `project_dir`: current project root
- `goal`: "Build pipeline PRD: $ARGUMENTS"
- `strategist_summary`: 1-2 sentence summary combining both strategists' positions
- `critic_summary`: 1-2 sentence summary of the critic's key concerns
- `decision`: your team-lead synthesis in 1-3 sentences
- `hub_lesson`: "Build pipeline Phase 1 complete. PRD written to .council/build/prd.md."
- `importance`: 7
- `pin`: false

### 1.6 Cleanup Phase 1

1. For each teammate: `SendMessage` with `type: "shutdown_request"`
2. `TeamDelete` to remove the team

Tell the user: "Phase 1 complete. PRD → `.council/build/prd.md`. Starting Phase 2: Tech Deck."

---

## PHASE 2: Tech Deck Consultation

> Roles: architect, strategist-alpha, security-auditor

### 2.1 Read PRD

Read `.council/build/prd.md`. This is the input for this phase.

### 2.2 Create team

Use `TeamCreate`:
- `team_name`: "council-build-tech"
- `description`: "Build pipeline Phase 2: Tech deck for <short goal>"

### 2.3 Spawn teammates (all in PARALLEL)

Launch ALL 3 teammates in the same message. All MUST include `team_name: "council-build-tech"` and a `name` parameter.

**Architect** — `name: "architect"`, `subagent_type: "the-council:architect"`:
```
GOAL: Create a technical architecture document for the following PRD.

PRD:
<full content of .council/build/prd.md>

MEMORY (from past consultations):
<memory from Step 1>

You are the Architect. Design the system architecture. 400-600 words.
Cover: technology stack recommendations, component architecture (with responsibilities and boundaries), data models/schema, API contracts, integration points, deployment architecture.
Be specific about file structure and naming conventions for the target project.
When done, send your full analysis to "team-lead" via SendMessage.
```

**Strategist Alpha** — `name: "strategist-alpha"`, `subagent_type: "the-council:strategist"`:
```
GOAL: Create a technical architecture document for the following PRD.

PRD:
<full content of .council/build/prd.md>

MEMORY (from past consultations):
<memory from Step 1>

You are Strategist Alpha (ambitious, forward-thinking). Propose technical approaches. 400-600 words.
Focus on: technology selection trade-offs, scalability path, developer experience, testing strategy, CI/CD pipeline, performance targets.
Push for the best possible technical foundation.
When done, send your full analysis to "team-lead" via SendMessage.
```

**Security Auditor** — `name: "security-auditor"`, `subagent_type: "the-council:security-auditor"`:
```
GOAL: Review the technical architecture for the following PRD.

PRD:
<full content of .council/build/prd.md>

MEMORY (from past consultations):
<memory from Step 1>

Audit the technical implications of this PRD. 400-600 words.
Focus on: authentication/authorization model, data protection, input validation, API security, dependency risks, secrets management, OWASP top 10 relevance.
Every finding MUST include a specific remediation.
When done, send your full analysis to "team-lead" via SendMessage.
```

Wait for all 3 teammates to send their analyses.

### 2.4 Synthesize Tech Deck

Apply standard synthesis rules. Format as a tech deck with these sections:
1. **Technology Stack** (with justification for each choice)
2. **Architecture Overview** (component diagram in text/ASCII)
3. **Component Design** (each component: responsibility, API surface, dependencies)
4. **Data Models** (key entities, relationships, schemas)
5. **API Contracts** (key endpoints/interfaces with request/response shapes)
6. **Security Architecture** (auth model, data protection, input validation)
7. **Testing Strategy** (unit, integration, e2e approach)
8. **Deployment & Infrastructure**
9. **File/Directory Structure** (proposed project layout)

### 2.5 Write Tech Deck artifact

Write the synthesized tech deck to `.council/build/tech-deck.md`.

### 2.6 Record Phase 2

Call `council_memory_record` with:
- `project_dir`: current project root
- `goal`: "Build pipeline Tech Deck: $ARGUMENTS"
- `strategist_summary`: 1-2 sentence summary of architect + strategist positions
- `critic_summary`: 1-2 sentence summary of the security auditor's key findings
- `decision`: your team-lead synthesis in 1-3 sentences
- `hub_lesson`: "Build pipeline Phase 2 complete. Tech deck written to .council/build/tech-deck.md."
- `importance`: 7
- `pin`: false

### 2.7 Cleanup Phase 2

1. For each teammate: `SendMessage` with `type: "shutdown_request"`
2. `TeamDelete` to remove the team

Tell the user: "Phase 2 complete. Tech deck → `.council/build/tech-deck.md`. Starting Phase 3: Backlog."

---

## PHASE 3: Backlog Consultation

> Roles: planner, strategist-beta, critic

### 3.1 Read artifacts

Read both:
- `.council/build/prd.md`
- `.council/build/tech-deck.md`

### 3.2 Create team

Use `TeamCreate`:
- `team_name`: "council-build-backlog"
- `description`: "Build pipeline Phase 3: Backlog for <short goal>"

### 3.3 Spawn teammates (all in PARALLEL)

Launch ALL 3 teammates in the same message. All MUST include `team_name: "council-build-backlog"` and a `name` parameter.

**Planner** — `name: "planner"`, `subagent_type: "the-council:planner"`:
```
GOAL: Create an implementation backlog for parallel dev teams based on the PRD and tech deck below.

PRD:
<full content of .council/build/prd.md>

TECH DECK:
<full content of .council/build/tech-deck.md>

MEMORY (from past consultations):
<memory from Step 1>

You are the Planner. Create a detailed implementation backlog. 500-700 words.
CRITICAL: Structure the backlog into 2-4 WORKSTREAMS that can be executed in parallel by independent dev teams.
Each workstream must:
- Have a clear name and scope
- List specific tasks as numbered items
- Note dependencies between tasks (within and across workstreams)
- Mark cross-workstream synchronization points
- Estimate relative complexity (S/M/L) for each task

Group by: foundation/setup, core features, secondary features, testing/polish.
When done, send your full analysis to "team-lead" via SendMessage.
```

**Strategist Beta** — `name: "strategist-beta"`, `subagent_type: "the-council:strategist"`:
```
GOAL: Create an implementation backlog for parallel dev teams based on the PRD and tech deck below.

PRD:
<full content of .council/build/prd.md>

TECH DECK:
<full content of .council/build/tech-deck.md>

MEMORY (from past consultations):
<memory from Step 1>

You are Strategist Beta (pragmatic, conservative). Review and propose a backlog. 500-700 words.
Focus on: task ordering that minimizes risk, shared foundation work before parallel work, tasks that could be descoped to MVP, integration risks between parallel workstreams.
When done, send your full analysis to "team-lead" via SendMessage.
```

**Critic** — `name: "critic"`, `subagent_type: "the-council:critic"`:
```
GOAL: Critique the implementation backlog plan for the following PRD and tech deck.

PRD:
<full content of .council/build/prd.md>

TECH DECK:
<full content of .council/build/tech-deck.md>

MEMORY (from past consultations):
<memory from Step 1>

Critique the implementation plan. 500-700 words. Start with the most critical issue.
Focus on: missing tasks, incorrect dependencies, parallelization risks (merge conflicts, interface mismatches), testing gaps, tasks too large or vague, missing error handling/edge cases.
Every issue needs a specific fix.
When done, send your full analysis to "team-lead" via SendMessage.
```

Wait for all 3 teammates to send their analyses.

### 3.4 Synthesize Backlog

Apply standard synthesis rules. Format as a backlog with these sections:

1. **Foundation Tasks** (must complete before parallel work begins)
   - Numbered tasks with complexity estimates (S/M/L)
2. **Workstream A: [Name]** (one dev team)
   - Numbered tasks with complexity estimates
   - Dependencies noted
3. **Workstream B: [Name]** (another dev team)
   - Numbered tasks with complexity estimates
   - Dependencies noted
4. **(Optional) Workstream C/D** if the project warrants it
5. **Synchronization Points** (where workstreams must integrate/verify)
6. **Post-Integration Tasks** (final testing, polish, deployment)

CRITICAL: The workstreams MUST be designed for parallel execution. Each workstream should be independently implementable with minimal cross-team blocking.

### 3.5 Write Backlog artifact

Write the synthesized backlog to `.council/build/backlog.md`.

### 3.6 Record Phase 3

Call `council_memory_record` with:
- `project_dir`: current project root
- `goal`: "Build pipeline Backlog: $ARGUMENTS"
- `strategist_summary`: 1-2 sentence summary of planner + strategist positions
- `critic_summary`: 1-2 sentence summary of the critic's key concerns
- `decision`: your team-lead synthesis in 1-3 sentences
- `hub_lesson`: "Build pipeline Phase 3 complete. Backlog written to .council/build/backlog.md."
- `importance`: 8
- `pin`: false

### 3.7 Cleanup Phase 3

1. For each teammate: `SendMessage` with `type: "shutdown_request"`
2. `TeamDelete` to remove the team

Tell the user: "Phase 3 complete. Backlog → `.council/build/backlog.md`. Starting Phase 4: Implementation."

---

## PHASE 4: Parallel Implementation

> This is NOT a consultation. This is actual code implementation using parallel dev teams.

### 4.1 Read all artifacts

Read:
- `.council/build/prd.md`
- `.council/build/tech-deck.md`
- `.council/build/backlog.md`

Parse the backlog to identify workstreams and their tasks.

### 4.2 Execute Foundation Tasks

Before spawning parallel teams, execute the **Foundation Tasks** from the backlog yourself (team-lead). These are setup tasks like:
- Creating project directory structure
- Initializing configuration files
- Installing dependencies
- Creating shared types/interfaces/models that both teams will need

This ensures parallel teams have a stable foundation to build on.

### 4.3 Plan team assignments

From the backlog, identify the workstreams. Create team assignments:
- **Minimum 2 teams, maximum 4 teams**
- Each team gets one or more workstreams
- Name teams: "build-team-alpha", "build-team-beta", "build-team-gamma", "build-team-delta"

### 4.4 Spawn dev teams (in PARALLEL)

For EACH dev team, use `TeamCreate` and then spawn a developer teammate via **Task tool**.

**Create each team:**
- `team_name`: "build-team-alpha" (or beta, gamma, delta)
- `description`: "Implementation team for workstream: <workstream name>"

**Spawn a developer teammate per team:**
- `name`: "dev-alpha" (or "dev-beta", etc.)
- `subagent_type`: "general-purpose" (needs full Write/Edit/Bash capabilities)
- `team_name`: the team name created above

Prompt for each developer:
```
You are a developer on <team-name>. Your job is to implement the following workstream.

PROJECT CONTEXT:
<brief summary from PRD: problem statement + core features relevant to this workstream>

TECH STACK:
<relevant sections from tech-deck.md: stack, file structure, data models>

YOUR WORKSTREAM TASKS:
<specific workstream tasks from backlog.md>

RULES:
1. Implement each task in order, respecting dependencies
2. Write working code — not pseudocode, not stubs
3. Include error handling and input validation
4. Add inline comments for complex logic only
5. Create tests for each component (unit tests minimum)
6. After completing each task, send a brief status update to "team-lead" via SendMessage
7. After completing ALL tasks, send a final summary to "team-lead" listing all files created/modified
8. If you encounter a blocker requiring the other team's output, send a message to "team-lead" and continue with the next non-blocked task
```

### 4.5 Coordinate implementation

As team-lead during implementation:
1. **Monitor progress**: Wait for status messages from dev teammates
2. **Handle blockers**: If a team reports a cross-team blocker, relay information between teams via `SendMessage`
3. **Track completion**: Keep track of which workstream tasks are done
4. **Do NOT implement code yourself** during this phase — only coordinate

### 4.6 Handle synchronization points

When all teams reach a synchronization point (as defined in the backlog):
1. Ask each team to pause and report current state
2. Verify interface compatibility between workstreams
3. If mismatches exist, instruct the relevant team to fix them
4. Give the go-ahead to continue past the sync point

### 4.7 Post-integration

After all workstream tasks are completed:
1. Review the list of all files created/modified
2. Execute **Post-Integration Tasks** from the backlog (integration tests, final wiring, configuration)
3. Run the project's test suite if one exists
4. Fix any integration issues

### 4.8 Cleanup Phase 4

For each dev team:
1. `SendMessage` with `type: "shutdown_request"` to each dev teammate
2. `TeamDelete` to remove each team

### 4.9 Record implementation

Call `council_memory_record` with:
- `project_dir`: current project root
- `goal`: "Build pipeline Implementation: $ARGUMENTS"
- `strategist_summary`: summary of what was built (files created, features implemented)
- `critic_summary`: any issues encountered during implementation and how they were resolved
- `decision`: "Implementation complete. <N> workstreams executed in parallel."
- `hub_lesson`: "Build pipeline completed for: <goal>. Artifacts in .council/build/."
- `importance`: 8
- `pin`: true

---

## Step Final: Present Results

Present to the user:

1. **Pipeline Summary** — Goal, phases completed (4/4), total agents spawned
2. **Artifacts** — `.council/build/prd.md`, `.council/build/tech-deck.md`, `.council/build/backlog.md`
3. **Implementation summary** — Teams used, files created/modified, test status
4. **Recorded to memory** — 4 consultations recorded, implementation pinned
5. **Next steps** — Review code, run tests, consider `/council:consult` for specific areas

---

## Error Handling

### If a consultation phase fails

1. Attempt cleanup: shutdown teammates, TeamDelete
2. Tell the user which phase failed and why
3. Offer to retry: "Phase <N> failed. Retry? (y/n)"
4. If retry fails, stop and suggest manual `/council:consult` for each phase

### If a dev team hangs or fails

1. Send a `SendMessage` asking for status
2. If no response: shutdown that team, tell user which workstream was incomplete
3. Continue with other teams — partial implementation is better than nothing
4. List incomplete tasks in the final presentation

### If artifacts are missing between phases

1. Check if the file exists before reading
2. If missing: "Artifact from Phase <N> not found. Run the pipeline again." and stop.
