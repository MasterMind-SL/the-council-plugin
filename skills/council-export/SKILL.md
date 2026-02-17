---
name: council-export
description: Export a consultation session as shareable markdown.
---

# Export Consultation

If $ARGUMENTS is provided, use it as the session ID.

Otherwise, call `tool_status` first to show recent sessions, then ask which session to export.

Call `tool_export` with `project_dir` (current project root, absolute path) and `session_id`.

Present the exported markdown to the user.
