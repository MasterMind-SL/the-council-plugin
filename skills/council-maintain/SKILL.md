---
name: council-maintain
description: Compact council memory files — deduplicate and clean up. Uses curator subagent to avoid polluting main session context.
---

# Council Memory Maintenance

## Step 1: Check memory health
Call `tool_maintain` with `project_dir` set to the current project root directory (absolute path).

## Step 2: If compaction is needed
Use the **Task tool** to launch the `curator` subagent with this prompt:

> Compact the council memory in `{project_dir}/.council/memory/`.
> Read both role log files, decisions.md, and lessons.jsonl.
> Write compacted active files. Report what you removed.

The curator runs in its own context window — zero cost to this session.

## Step 3: Report
Show the user what was compacted and the before/after line counts.
