---
name: council-update
description: Migrate council data after a plugin update. Handles version transitions and schema changes.
---

# Update Council

Run this after updating The Council plugin to a new version. Migrates `.council/` data and reports what's new.

## Step 1: Check initialization

Check if `.council/` exists in the current project directory. If not, tell the user: "No council found. Run `/council:init` to start fresh with v3.0.0." and stop.

## Step 2: Read current version

Read `.council/memory/index.json`. Check for the `plugin_version` field:
- If `plugin_version` exists: that's the installed version.
- If `plugin_version` is missing: this is a **pre-v3.0.0 installation** (v2.x or earlier).

## Step 3: Run migrations

### From v2.x (no plugin_version) to v3.0.0

1. **Add version tracking**: Add `"plugin_version": "3.0.0"` to `index.json` and save it.

2. **Preserve all existing data**: Do NOT delete or modify existing decisions, lessons, active memory, or archives. All v2.x memory is fully compatible with v3.0.0.

3. **Report what's new in v3.0.0**:
   - 4 consultation modes (default, debate, plan, reflect) — auto-routed, no flags needed
   - Configurable roles via `ROLES:` clause (architect, security-auditor, ux-reviewer, planner, or custom)
   - Debate mode with 1 rebuttal round (teammates cross-read positions)
   - Plan mode outputs numbered steps with P0/P1/P2 priorities
   - Reflect mode analyzes your decision history and recommends future consultations
   - "Hub" renamed to "team-lead" in all protocols and documentation

### From v3.0.0 to v3.0.0 (already current)

Report: "Already on v3.0.0. No migration needed." and stop.

### Future migrations (template)

When new versions are released, add migration blocks here:

```
### From v3.0.0 to v3.x.x
1. <migration step>
2. <migration step>
3. Update plugin_version to "3.x.x" in index.json
```

## Step 4: Verify integrity

After migration, run a quick health check:
1. Call `council_memory_status` with `project_dir`
2. Check that consultation_count, recent_decisions, and memory health look correct
3. If any issues, report them and suggest `/council:reset` (soft) or `/council:init` (fresh start)

## Step 5: Report

Present to the user:
1. Previous version (or "pre-v3.0.0" if no plugin_version was found)
2. Current version after migration
3. What was migrated (list each change)
4. What's new in this version (brief feature summary)
5. Memory health status
6. Next steps: "Run `/council:consult` to use the new features."
