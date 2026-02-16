---
name: reset
description: Clear council session data. Pass --all to also clear memory.
---

# Council Reset

If $ARGUMENTS contains "--all", call `tool_reset` with `project_dir` and `full=true`.
Otherwise call `tool_reset` with `project_dir` and `full=false`.

If doing a full reset, confirm with the user first before calling the tool.

Report what was cleared.
