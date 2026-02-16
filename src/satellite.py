"""Satellite spawning — launches claude -p subprocesses for adversarial consultation."""

import asyncio
import os
import shutil
from pathlib import Path

from .config import get_config


async def spawn_satellite(
    role: str,
    goal: str,
    session_id: str,
    project_dir: str,
    plugin_root: str,
) -> dict:
    """Spawn a single satellite via claude -p subprocess."""
    config = get_config(project_dir)

    agent_def_path = Path(plugin_root) / "agents" / f"{role}.md"
    memory_active = Path(project_dir) / ".council" / "memory" / f"{role}-active.md"
    memory_log = Path(project_dir) / ".council" / "memory" / f"{role}-log.md"
    output_file = Path(project_dir) / ".council" / "bus" / "satellites" / f"{session_id}-{role}.md"
    log_file = Path(project_dir) / ".council" / "logs" / f"{session_id}-{role}.log"

    # Ensure directories
    output_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Validate agent definition
    if not agent_def_path.exists():
        return {
            "role": role,
            "success": False,
            "error": f"Agent definition not found: {agent_def_path}",
            "output": "",
            "exit_code": 1,
        }

    agent_def = agent_def_path.read_text(encoding="utf-8")

    # Build system prompt: agent definition + persistent memory + output instructions
    system_parts = [agent_def, "\n\n---\n\n## Your Persistent Memory\n\n"]

    if memory_active.exists():
        content = memory_active.read_text(encoding="utf-8")
        if content.strip() and "*No compacted memory yet.*" not in content:
            system_parts.append(content)
        else:
            system_parts.append("*No prior memory.*")
    elif memory_log.exists():
        content = memory_log.read_text(encoding="utf-8")
        if content.strip() and "*No sessions yet.*" not in content:
            system_parts.append(content)
        else:
            system_parts.append("*No prior memory.*")
    else:
        system_parts.append("*No prior memory.*")

    system_parts.append("\n\n---\n\n## Output Instructions\n\n")
    system_parts.append(f"Write your complete analysis to: `{output_file}`\n")
    system_parts.append("Use the Write tool to create this file. 300-500 words. Start with your recommendation.\n")

    system_prompt = "".join(system_parts)

    # Write temp files in .council/.tmp (Windows /tmp is unreliable for claude -p subprocesses)
    tmp_dir = Path(project_dir) / ".council" / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    system_file = tmp_dir / f"system-{role}-{session_id}.md"
    system_file.write_text(system_prompt, encoding="utf-8")

    # Find claude executable
    claude_cmd = shutil.which("claude")
    if not claude_cmd:
        for candidate in ["claude.cmd", "claude.exe"]:
            found = shutil.which(candidate)
            if found:
                claude_cmd = found
                break

    if not claude_cmd:
        system_file.unlink(missing_ok=True)
        return {
            "role": role,
            "success": False,
            "error": "claude executable not found on PATH",
            "output": "",
            "exit_code": 1,
        }

    # Build command — designed for Max accounts (no budget caps)
    cmd = [
        claude_cmd, "-p",
        "--model", config["model"],
        "--fallback-model", config["fallback"],
        "--append-system-prompt-file", str(system_file),
        "--allowedTools", "Read,Write,Glob,Grep,Bash,WebFetch,WebSearch,Task",
        "--max-turns", str(config["max_turns"]),
        "--no-session-persistence",
        "--output-format", "stream-json",
    ]

    # Remove CLAUDECODE env to avoid subprocess detection issues
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=project_dir,
            env=env,
        )

        stdout_data, _ = await asyncio.wait_for(
            proc.communicate(input=goal.encode("utf-8")),
            timeout=300,  # 5 minute timeout per satellite
        )

        # Write log
        log_file.write_bytes(stdout_data)

    except asyncio.TimeoutError:
        proc.kill()
        system_file.unlink(missing_ok=True)
        return {
            "role": role,
            "success": False,
            "error": "Satellite timed out after 5 minutes",
            "output": "",
            "exit_code": -1,
            "log_file": str(log_file),
        }
    except Exception as e:
        system_file.unlink(missing_ok=True)
        return {
            "role": role,
            "success": False,
            "error": str(e),
            "output": "",
            "exit_code": -1,
        }
    finally:
        system_file.unlink(missing_ok=True)

    # Read output
    output = ""
    if output_file.exists():
        output = output_file.read_text(encoding="utf-8")

    exit_code = proc.returncode or 0
    success = exit_code == 0 and output_file.exists() and len(output.strip()) > 0

    return {
        "role": role,
        "exit_code": exit_code,
        "output": output,
        "output_file": str(output_file),
        "log_file": str(log_file),
        "success": success,
    }


async def spawn_both(
    goal: str,
    session_id: str,
    project_dir: str,
    plugin_root: str,
) -> dict:
    """Spawn strategist + critic in parallel. Wait for both."""
    results = await asyncio.gather(
        spawn_satellite("strategist", goal, session_id, project_dir, plugin_root),
        spawn_satellite("critic", goal, session_id, project_dir, plugin_root),
        return_exceptions=True,
    )

    output = {"session_id": session_id}

    for i, role in enumerate(["strategist", "critic"]):
        result = results[i]
        if isinstance(result, Exception):
            output[role] = {
                "role": role,
                "success": False,
                "error": str(result),
                "output": "",
                "exit_code": -1,
            }
        else:
            output[role] = result

    return output
