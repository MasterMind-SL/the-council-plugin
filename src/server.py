"""The Council MCP Server — Adversarial consultation with strategist + critic satellites."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .config import get_plugin_root
from .satellite import spawn_both

mcp = FastMCP("the-council")


def _council_dir(project_dir: str) -> Path:
    return Path(project_dir) / ".council"


def _check_init(project_dir: str) -> str | None:
    council = _council_dir(project_dir)
    if not council.exists():
        return f"Council not initialized in {project_dir}. Call tool_init first."
    return None


# ---------------------------------------------------------------------------
# Tool: init
# ---------------------------------------------------------------------------
@mcp.tool()
async def tool_init(project_dir: str) -> str:
    """Initialize The Council in a project directory.

    Creates .council/ with memory, bus/satellites, and logs subdirectories.
    Adds ephemeral paths to .gitignore.

    Args:
        project_dir: Absolute path to the project root directory.
    """
    council = _council_dir(project_dir)

    if council.exists():
        return f"Council already initialized at {council}. Use tool_reset(full=True) to reinitialize."

    # Create directories
    (council / "memory").mkdir(parents=True, exist_ok=True)
    (council / "bus" / "satellites").mkdir(parents=True, exist_ok=True)
    (council / "logs").mkdir(parents=True, exist_ok=True)

    # Initial memory files
    (council / "memory" / "strategist-log.md").write_text(
        "# Strategist Memory Log\n\n*No sessions yet.*\n", encoding="utf-8"
    )
    (council / "memory" / "strategist-active.md").write_text(
        "# Strategist Active Memory\n\n*No compacted memory yet.*\n", encoding="utf-8"
    )
    (council / "memory" / "critic-log.md").write_text(
        "# Critic Memory Log\n\n*No sessions yet.*\n", encoding="utf-8"
    )
    (council / "memory" / "critic-active.md").write_text(
        "# Critic Active Memory\n\n*No compacted memory yet.*\n", encoding="utf-8"
    )
    (council / "memory" / "decisions.md").write_text(
        "# Hub Decision Record\n\n*No decisions yet.*\n", encoding="utf-8"
    )
    (council / "memory" / "lessons.jsonl").write_text("", encoding="utf-8")
    (council / "bus" / "feed.jsonl").write_text("", encoding="utf-8")

    # .gitignore — exclude ephemeral state, keep memory
    gitignore = Path(project_dir) / ".gitignore"
    entries = "\n# Council ephemeral state\n.council/bus/satellites/\n.council/logs/\n.council/.tmp/\n"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if ".council/bus/satellites/" not in content:
            with open(gitignore, "a", encoding="utf-8") as f:
                f.write(entries)
    else:
        gitignore.write_text(entries, encoding="utf-8")

    return (
        f"Council initialized at {council}.\n\n"
        "Directories created:\n"
        "- .council/memory/ (persistent — decisions, lessons, satellite learnings)\n"
        "- .council/bus/ (feed + satellite outputs)\n"
        "- .council/logs/ (ephemeral)\n\n"
        "Run tool_consult to start your first consultation."
    )


# ---------------------------------------------------------------------------
# Tool: consult
# ---------------------------------------------------------------------------
@mcp.tool()
async def tool_consult(goal: str, project_dir: str, session_id: str = "") -> str:
    """Spawn strategist + critic satellites for adversarial consultation.

    Launches two parallel claude -p processes. Each satellite writes its
    analysis independently. Returns both analyses for the hub (you) to synthesize.

    After reading both analyses, YOU must:
    1. Present both to the user
    2. Synthesize: where they agree (adopt), conflict (YOU resolve), one raises
       something the other missed (incorporate)
    3. Call tool_record with your decision

    One round only. No re-consultation. No loops.

    Use for: architecture decisions, complex implementations, risk analysis,
    security audits. Simple tasks should be answered directly.

    Args:
        goal: The consultation goal — be specific and actionable.
        project_dir: Absolute path to the project root (must have .council/).
        session_id: Optional session identifier. Auto-generated if empty.
    """
    error = _check_init(project_dir)
    if error:
        return error

    if not session_id:
        session_id = str(int(time.time()))

    plugin_root = get_plugin_root()

    # Spawn both satellites in parallel
    results = await spawn_both(goal, session_id, project_dir, plugin_root)

    # Format response
    parts = [f"## Council Session {session_id}\n"]
    parts.append(f"**Goal**: {goal}\n")

    for role in ["strategist", "critic"]:
        info = results[role]
        label = "Strategist Analysis" if role == "strategist" else "Critic Analysis"
        parts.append(f"\n### {label}\n")
        if info["success"]:
            parts.append(info["output"])
        else:
            error_msg = info.get("error", f"Exit code {info.get('exit_code', 'unknown')}")
            parts.append(f"**FAILED**: {error_msg}")
            if info.get("log_file"):
                parts.append(f"\nCheck log: `{info['log_file']}`")

    parts.append(
        f"\n---\n\n"
        f"**Your turn, Hub.** Synthesize both analyses above, then call "
        f"`tool_record` with session_id='{session_id}'."
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Tool: record
# ---------------------------------------------------------------------------
@mcp.tool()
async def tool_record(
    project_dir: str,
    session_id: str,
    goal: str,
    strategist_summary: str,
    critic_summary: str,
    decision: str,
    strategist_lesson: str = "",
    critic_lesson: str = "",
    hub_lesson: str = "",
) -> str:
    """Record consultation results to memory files.

    Appends to: feed.jsonl, decisions.md, lessons.jsonl, and role memory logs.
    Call this after synthesizing satellite outputs from tool_consult.

    Args:
        project_dir: Project root directory.
        session_id: Session ID from tool_consult.
        goal: The original consultation goal.
        strategist_summary: 1-2 sentence summary of strategist's position.
        critic_summary: 1-2 sentence summary of critic's position.
        decision: Your hub decision and reasoning (1-3 sentences).
        strategist_lesson: Optional reusable insight from strategist.
        critic_lesson: Optional reusable insight from critic.
        hub_lesson: Optional meta-lesson from the hub synthesis.
    """
    error = _check_init(project_dir)
    if error:
        return error

    council = _council_dir(project_dir)
    now = datetime.now(timezone.utc).isoformat()
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Append to feed.jsonl
    feed = council / "bus" / "feed.jsonl"
    feed_entries = [
        {"ts": now, "from": "hub", "type": "goal", "summary": goal},
        {"ts": now, "from": "hub", "type": "spawn", "summary": f"Launched strategist + critic (session {session_id})"},
        {"ts": now, "from": "hub", "type": "synthesis", "summary": decision[:200]},
        {"ts": now, "from": "hub", "type": "decision", "summary": decision},
    ]
    with open(feed, "a", encoding="utf-8") as f:
        for entry in feed_entries:
            f.write(json.dumps(entry) + "\n")

    # Append to decisions.md
    decisions_file = council / "memory" / "decisions.md"
    with open(decisions_file, "a", encoding="utf-8") as f:
        f.write(f"\n## {date_str} — {goal[:80]} (session {session_id})\n\n")
        f.write(f"- **Goal:** {goal}\n")
        f.write(f"- **Strategist:** {strategist_summary}\n")
        f.write(f"- **Critic:** {critic_summary}\n")
        f.write(f"- **Decision:** {decision}\n\n")

    # Append lessons
    lessons_file = council / "memory" / "lessons.jsonl"
    with open(lessons_file, "a", encoding="utf-8") as f:
        if strategist_lesson:
            f.write(json.dumps({"ts": now, "lesson": strategist_lesson, "source": "strategist"}) + "\n")
        if critic_lesson:
            f.write(json.dumps({"ts": now, "lesson": critic_lesson, "source": "critic"}) + "\n")
        if hub_lesson:
            f.write(json.dumps({"ts": now, "lesson": hub_lesson, "source": "hub"}) + "\n")

    # Append to role memory logs
    for role, lesson in [("strategist", strategist_lesson), ("critic", critic_lesson)]:
        if lesson:
            log_file = council / "memory" / f"{role}-log.md"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n### Session {session_id} ({date_str})\n\n{lesson}\n")

    return f"Recorded consultation {session_id}. Decision saved to memory/decisions.md."


# ---------------------------------------------------------------------------
# Tool: status
# ---------------------------------------------------------------------------
@mcp.tool()
async def tool_status(project_dir: str) -> str:
    """Show Council state for this project.

    Returns: recent decisions, memory summary, feed activity, and stats.

    Args:
        project_dir: Project root directory.
    """
    error = _check_init(project_dir)
    if error:
        return error

    council = _council_dir(project_dir)
    parts = ["# Council Status\n"]

    # Recent decisions
    decisions_file = council / "memory" / "decisions.md"
    if decisions_file.exists():
        content = decisions_file.read_text(encoding="utf-8")
        sections = content.split("\n## ")
        if len(sections) > 1:
            recent = sections[-3:] if len(sections) > 3 else sections[1:]
            parts.append("## Recent Decisions\n")
            for s in recent:
                parts.append(f"## {s}")
        else:
            parts.append("## Decisions\n*No decisions yet.*\n")

    # Memory summary
    parts.append("\n## Memory Summary\n")
    for role in ["strategist", "critic"]:
        active = council / "memory" / f"{role}-active.md"
        log = council / "memory" / f"{role}-log.md"
        if active.exists():
            lines = active.read_text(encoding="utf-8").strip().split("\n")
            parts.append(f"- **{role.title()}**: {len(lines)} lines (active)")
        elif log.exists():
            lines = log.read_text(encoding="utf-8").strip().split("\n")
            parts.append(f"- **{role.title()}**: {len(lines)} lines (log only)")

    # Feed activity
    feed_file = council / "bus" / "feed.jsonl"
    if feed_file.exists():
        lines = [l for l in feed_file.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
        parts.append(f"\n## Feed Activity\n\nTotal events: {len(lines)}\n")
        if lines:
            parts.append("| Time | From | Type | Summary |")
            parts.append("|------|------|------|---------|")
            for line in lines[-10:]:
                try:
                    entry = json.loads(line)
                    ts = entry.get("ts", "?")[:19]
                    parts.append(
                        f"| {ts} | {entry.get('from', '?')} | {entry.get('type', '?')} "
                        f"| {entry.get('summary', '?')[:60]} |"
                    )
                except json.JSONDecodeError:
                    pass

    # Stats
    satellites_dir = council / "bus" / "satellites"
    satellite_count = len(list(satellites_dir.glob("*.md"))) if satellites_dir.exists() else 0

    lessons_file = council / "memory" / "lessons.jsonl"
    lesson_count = 0
    if lessons_file.exists():
        lesson_count = len([l for l in lessons_file.read_text(encoding="utf-8").strip().split("\n") if l.strip()])

    decision_count = 0
    if decisions_file.exists():
        decision_count = decisions_file.read_text(encoding="utf-8").count("\n## ")

    parts.append(f"\n## Stats\n")
    parts.append(f"- Consultations: {decision_count}")
    parts.append(f"- Satellite outputs: {satellite_count}")
    parts.append(f"- Lessons: {lesson_count}")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Tool: reset
# ---------------------------------------------------------------------------
@mcp.tool()
async def tool_reset(project_dir: str, full: bool = False) -> str:
    """Clear council session data.

    Session reset (default): clears satellites, logs, and feed. Keeps memory.
    Full reset (full=True): also clears all memory and decisions.

    Args:
        project_dir: Project root directory.
        full: If True, also clear memory (strategist, critic, decisions, lessons).
    """
    error = _check_init(project_dir)
    if error:
        return error

    council = _council_dir(project_dir)
    removed = []

    # Clear satellites
    sat_dir = council / "bus" / "satellites"
    if sat_dir.exists():
        count = sum(1 for f in sat_dir.glob("*") if f.is_file())
        for f in sat_dir.glob("*"):
            if f.is_file():
                f.unlink()
        removed.append(f"{count} satellite files")

    # Clear logs
    log_dir = council / "logs"
    if log_dir.exists():
        count = sum(1 for f in log_dir.glob("*") if f.is_file())
        for f in log_dir.glob("*"):
            if f.is_file():
                f.unlink()
        removed.append(f"{count} log files")

    # Clear tmp
    tmp_dir = council / ".tmp"
    if tmp_dir.exists():
        for f in tmp_dir.glob("*"):
            if f.is_file():
                f.unlink()

    # Truncate feed
    feed = council / "bus" / "feed.jsonl"
    if feed.exists():
        feed.write_text("", encoding="utf-8")
        removed.append("feed.jsonl")

    if full:
        (council / "memory" / "strategist-log.md").write_text(
            "# Strategist Memory Log\n\n*No sessions yet.*\n", encoding="utf-8"
        )
        (council / "memory" / "strategist-active.md").write_text(
            "# Strategist Active Memory\n\n*No compacted memory yet.*\n", encoding="utf-8"
        )
        (council / "memory" / "critic-log.md").write_text(
            "# Critic Memory Log\n\n*No sessions yet.*\n", encoding="utf-8"
        )
        (council / "memory" / "critic-active.md").write_text(
            "# Critic Active Memory\n\n*No compacted memory yet.*\n", encoding="utf-8"
        )
        (council / "memory" / "decisions.md").write_text(
            "# Hub Decision Record\n\n*No decisions yet.*\n", encoding="utf-8"
        )
        (council / "memory" / "lessons.jsonl").write_text("", encoding="utf-8")
        removed.append("all memory files")
        return f"Full reset complete. Cleared: {', '.join(removed)}."

    return f"Session reset. Cleared: {', '.join(removed)}. Memory preserved."


# ---------------------------------------------------------------------------
# Tool: maintain
# ---------------------------------------------------------------------------
@mcp.tool()
async def tool_maintain(project_dir: str) -> str:
    """Check memory health and report stats. Actual compaction is done by the
    curator subagent (agents/curator.md) via the /council:maintain skill.

    Returns memory line counts so the skill can decide whether to invoke the curator.

    Args:
        project_dir: Project root directory.
    """
    error = _check_init(project_dir)
    if error:
        return error

    council = _council_dir(project_dir)
    parts = ["## Memory Health\n"]

    needs_compaction = False
    for role in ["strategist", "critic"]:
        log_file = council / "memory" / f"{role}-log.md"
        active_file = council / "memory" / f"{role}-active.md"

        log_lines = 0
        active_lines = 0
        if log_file.exists():
            log_lines = len(log_file.read_text(encoding="utf-8").strip().split("\n"))
        if active_file.exists():
            active_lines = len(active_file.read_text(encoding="utf-8").strip().split("\n"))

        status = "OK"
        if log_lines > 150:
            status = "COMPACT RECOMMENDED"
            needs_compaction = True
        elif log_lines > 80 and active_lines == 0:
            status = "COMPACT SUGGESTED"
            needs_compaction = True

        parts.append(f"- **{role}**: log={log_lines} lines, active={active_lines} lines — {status}")

    lessons_file = council / "memory" / "lessons.jsonl"
    if lessons_file.exists():
        lesson_count = len([l for l in lessons_file.read_text(encoding="utf-8").strip().split("\n") if l.strip()])
        parts.append(f"- **lessons**: {lesson_count} entries")

    if needs_compaction:
        parts.append("\nInvoke the **curator** subagent to compact memory. Use Task tool with agents/curator.md.")
    else:
        parts.append("\nMemory is healthy. No compaction needed.")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Tool: export
# ---------------------------------------------------------------------------
@mcp.tool()
async def tool_export(project_dir: str, session_id: str) -> str:
    """Export a consultation session as shareable markdown.

    Combines satellite outputs and decision record into a single document.

    Args:
        project_dir: Project root directory.
        session_id: The session ID to export (from tool_consult).
    """
    error = _check_init(project_dir)
    if error:
        return error

    council = _council_dir(project_dir)

    strat_file = council / "bus" / "satellites" / f"{session_id}-strategist.md"
    critic_file = council / "bus" / "satellites" / f"{session_id}-critic.md"

    if not strat_file.exists() and not critic_file.exists():
        return f"No satellite outputs found for session {session_id}."

    parts = [f"# Council Consultation — Session {session_id}\n"]
    parts.append(f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    # Find decision
    decisions_file = council / "memory" / "decisions.md"
    if decisions_file.exists():
        content = decisions_file.read_text(encoding="utf-8")
        sections = content.split("\n## ")
        for section in sections:
            if session_id in section:
                parts.append(f"\n## Decision Record\n\n## {section}")
                break

    if strat_file.exists():
        parts.append(f"\n## Strategist Analysis\n\n{strat_file.read_text(encoding='utf-8')}")

    if critic_file.exists():
        parts.append(f"\n## Critic Analysis\n\n{critic_file.read_text(encoding='utf-8')}")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="stdio")
