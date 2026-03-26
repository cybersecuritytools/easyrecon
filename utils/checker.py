"""
easyrecon Tool Checker & Auto-Installer
Checks tool availability and installs missing tools.
"""

import shutil
import subprocess
import sys
from typing import Dict, Tuple

from utils.registry import TOOL_REGISTRY, PHASE_TOOLS
from utils.config import Config


class ToolStatus:
    INSTALLED = "installed"
    MISSING = "missing"
    INSTALLING = "installing"
    INSTALLED_NOW = "installed_now"
    INSTALL_FAILED = "install_failed"
    DISABLED = "disabled"


def check_go() -> bool:
    """Check if Go is installed."""
    return shutil.which("go") is not None


def check_all_tools(config: Config) -> Dict[str, str]:
    """
    Check status of all tools in registry.

    Returns:
        Dict of tool_name → status string
    """
    statuses = {}
    for tool_name, tool_data in TOOL_REGISTRY.items():
        if not config.is_tool_enabled(tool_name):
            statuses[tool_name] = ToolStatus.DISABLED
        elif shutil.which(tool_data["cmd"]):
            statuses[tool_name] = ToolStatus.INSTALLED
        else:
            statuses[tool_name] = ToolStatus.MISSING
    return statuses


def get_tool_version(tool_name: str) -> str:
    """Try to get tool version string."""
    cmd = TOOL_REGISTRY[tool_name]["cmd"]
    for flag in ["-version", "--version", "version"]:
        try:
            result = subprocess.run(
                [cmd, flag],
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = (result.stdout + result.stderr).strip()
            if output:
                first_line = output.splitlines()[0]
                return first_line[:40]
        except Exception:
            continue
    return "installed"


def auto_install_missing(
    config: Config,
    display_callback=None,
) -> Dict[str, str]:
    """
    Auto-install all missing tools that are enabled.

    Args:
        config: Config object
        display_callback: Optional callable(tool_name, status, message)

    Returns:
        Updated status dict
    """
    if not check_go():
        return {}

    statuses = check_all_tools(config)
    updated = dict(statuses)

    for tool_name, status in statuses.items():
        if status != ToolStatus.MISSING:
            continue

        tool_data = TOOL_REGISTRY[tool_name]

        if display_callback:
            display_callback(tool_name, ToolStatus.INSTALLING, "installing...")

        success = _install_tool(tool_name, tool_data["install_cmd"])

        if success:
            updated[tool_name] = ToolStatus.INSTALLED_NOW
            if display_callback:
                display_callback(tool_name, ToolStatus.INSTALLED_NOW, "installed successfully")
        else:
            updated[tool_name] = ToolStatus.INSTALL_FAILED
            if display_callback:
                display_callback(
                    tool_name,
                    ToolStatus.INSTALL_FAILED,
                    f"install failed — run: {tool_data['install_cmd']}",
                )

    return updated


def _install_tool(tool_name: str, install_cmd: str) -> bool:
    """
    Run go install for a tool.

    Returns:
        True if install succeeded
    """
    parts = install_cmd.strip().split()
    try:
        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            timeout=300,
        )
        cmd_binary = TOOL_REGISTRY[tool_name]["cmd"]
        return result.returncode == 0 and shutil.which(cmd_binary) is not None
    except Exception:
        return False


def check_phase_tools(phase: str, config: Config) -> Tuple[bool, list, list]:
    """
    Check if a phase has enough tools to run.

    Args:
        phase: Phase name (subdomain, urls, live)
        config: Config object

    Returns:
        (can_run, available_tools, missing_tools)
    """
    phase_tools = PHASE_TOOLS.get(phase, [])
    available = []
    missing = []

    for tool_name in phase_tools:
        if not config.is_tool_enabled(tool_name):
            continue
        tool_data = TOOL_REGISTRY[tool_name]
        if shutil.which(tool_data["cmd"]):
            available.append(tool_name)
        else:
            missing.append(tool_name)

    has_critical_missing = any(
        TOOL_REGISTRY[t]["critical"] for t in missing
        if t in TOOL_REGISTRY
    )

    can_run = len(available) > 0 and not has_critical_missing
    return can_run, available, missing
