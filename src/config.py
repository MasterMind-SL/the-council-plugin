"""Configuration for The Council MCP server."""

import os
from pathlib import Path


def get_plugin_root() -> str:
    """Get the plugin root directory."""
    return os.environ.get(
        "CLAUDE_PLUGIN_ROOT",
        str(Path(__file__).parent.parent),
    )


def get_config(project_dir: str) -> dict:
    """Get council configuration with optional .council/config.yaml overrides."""
    config = {
        "model": "opus",
        "fallback": "sonnet",
        "max_turns": 10,
    }

    config_file = Path(project_dir) / ".council" / "config.yaml"
    if config_file.exists():
        try:
            import yaml

            with open(config_file, encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}

            model = user_config.get("model", {})
            if "default" in model:
                config["model"] = model["default"]
            if "fallback" in model:
                config["fallback"] = model["fallback"]

            limits = user_config.get("limits", {})
            if "max_turns" in limits:
                config["max_turns"] = limits["max_turns"]
        except Exception:
            pass  # Use defaults on any config error

    return config
