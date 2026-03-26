"""
easyrecon Dynamic Tool Runner
3-layer decision: disabled → missing → execute
"""

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Optional

from utils.registry import TOOL_REGISTRY
from utils.config import Config

from utils.registry import TOOL_REGISTRY
from utils.config import Config


class CriticalToolMissing(Exception):
    """Raised when a critical tool is unavailable."""
    pass


class ToolResult:
    """Result from running a tool."""

    def __init__(
        self,
        tool_name: str,
        lines: List[str],
        elapsed: float,
        status: str,
        message: str = "",
    ) -> None:
        self.tool_name = tool_name
        self.lines = lines
        self.elapsed = elapsed
        self.status = status
        self.message = message
        self.count = len(lines)


def run_tool(
    tool_name: str,
    target_or_input: str,
    config: Config,
    input_file: Optional[Path] = None,
) -> ToolResult:
    """
    Run an external tool through the 3-layer decision tree.

    Args:
        tool_name: Key in TOOL_REGISTRY
        target_or_input: Domain or input value
        config: Global config object
        input_file: Path to input file (for httpx -l flag)

    Returns:
        ToolResult with lines, elapsed time, and status
    """
    start = time.time()

    # LAYER 1 — Config check
    if not config.is_tool_enabled(tool_name):
        return ToolResult(
            tool_name=tool_name,
            lines=[],
            elapsed=0.0,
            status="disabled",
            message="disabled in config",
        )

    # LAYER 2 — Availability check
    tool_data = TOOL_REGISTRY[tool_name]
    cmd_binary = tool_data["cmd"]

    if not shutil.which(cmd_binary):
        if config.no_install or not config.auto_install:
            if tool_data["critical"]:
                raise CriticalToolMissing(
                    f"{tool_name} is required but not installed.\n"
                    f"Install: {tool_data['install_cmd']}"
                )
            return ToolResult(
                tool_name=tool_name,
                lines=[],
                elapsed=0.0,
                status="missing",
                message=f"not found — install: {tool_data['install_cmd']}",
            )

        install_result = _attempt_install(tool_name, tool_data["install_cmd"])
        if not install_result:
            if tool_data["critical"]:
                raise CriticalToolMissing(
                    f"{tool_name} install failed.\n"
                    f"Install manually: {tool_data['install_cmd']}"
                )
            return ToolResult(
                tool_name=tool_name,
                lines=[],
                elapsed=0.0,
                status="install_failed",
                message=f"install failed — run manually: {tool_data['install_cmd']}",
            )

    # LAYER 3 — Execution
    cmd = _build_command(tool_name, tool_data, target_or_input, input_file, config)
    timeout = config.get_tool_timeout(tool_name)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.time() - start

        if proc.returncode != 0:
            err = (proc.stderr or "").strip().splitlines()
            err_msg = err[0] if err else f"process exited with {proc.returncode}"
            return ToolResult(
                tool_name=tool_name,
                lines=[],
                elapsed=elapsed,
                status="error",
                message=err_msg,
            )

        lines = _parse_output(proc.stdout)

        if not lines:
            stderr_lines = _parse_output(proc.stderr)
            if stderr_lines:
                return ToolResult(
                    tool_name=tool_name,
                    lines=[],
                    elapsed=elapsed,
                    status="error",
                    message=stderr_lines[0],
                )

        return ToolResult(
            tool_name=tool_name,
            lines=lines,
            elapsed=elapsed,
            status="success" if lines else "empty",
            message="" if lines else "0 results",
        )

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return ToolResult(
            tool_name=tool_name,
            lines=[],
            elapsed=elapsed,
            status="timeout",
            message=f"timeout after {int(elapsed)}s",
        )

    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start
        return ToolResult(
            tool_name=tool_name,
            lines=[],
            elapsed=elapsed,
            status="error",
            message=f"process error: {e.returncode}",
        )

    except FileNotFoundError:
        elapsed = time.time() - start
        return ToolResult(
            tool_name=tool_name,
            lines=[],
            elapsed=elapsed,
            status="missing",
            message="binary disappeared during run",
        )

    except Exception as e:
        elapsed = time.time() - start
        return ToolResult(
            tool_name=tool_name,
            lines=[],
            elapsed=elapsed,
            status="error",
            message=str(e),
        )


def _build_command(
    tool_name: str,
    tool_data: dict,
    target: str,
    input_file: Optional[Path],
    config: Config,
) -> List[str]:
    """Build the final command list for subprocess."""
    cmd = [tool_data["cmd"]]
    input_value = str(input_file) if input_file else target

    for arg in tool_data["args"]:
        # Support placeholders embedded in larger args (e.g. http://{target}).
        rendered = arg.replace("{target}", target).replace("{input}", input_value)
        cmd.append(rendered)

    extra = config.get_tool_extra_args(tool_name)
    cmd.extend(extra)

    return cmd


def _parse_output(stdout: str) -> List[str]:
    """Parse stdout into clean list of non-empty lines."""
    if not stdout:
        return []
    lines = [line.strip() for line in stdout.splitlines()]
    return [line for line in lines if line]


def _attempt_install(tool_name: str, install_cmd: str) -> bool:
    """
    Attempt to install a tool via go install.

    Returns:
        True if install succeeded, False otherwise
    """
    if not shutil.which("go"):
        return False

    parts = install_cmd.split()

    try:
        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            timeout=300,
        )
        return result.returncode == 0 and shutil.which(tool_name.split("/")[-1]) is not None
    except Exception:
        return False