"""
easyrecon Configuration System
Loads config from yaml file with fallback to defaults.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from utils.registry import TOOL_REGISTRY


@dataclass
class ToolConfig:
    """Per-tool configuration."""
    enabled: bool = True
    timeout: int = 120
    extra_args: str = ""


@dataclass
class Config:
    """Main easyrecon configuration."""
    target: str = ""
    output_dir: Path = Path("./results")
    phase: Optional[str] = None
    timeout: int = 120
    auto_install: bool = True
    save_raw: bool = True
    threads: int = 50
    config_file: Optional[Path] = None
    no_install: bool = False
    tools: Dict[str, ToolConfig] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize tool configs from registry."""
        for tool_name, tool_data in TOOL_REGISTRY.items():
            if tool_name not in self.tools:
                self.tools[tool_name] = ToolConfig(
                    enabled=tool_data["enabled"],
                    timeout=tool_data["timeout"],
                    extra_args="",
                )

    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a tool is enabled in config."""
        if tool_name in self.tools:
            return self.tools[tool_name].enabled
        return TOOL_REGISTRY.get(tool_name, {}).get("enabled", True)

    def get_tool_timeout(self, tool_name: str) -> int:
        """Get timeout for a tool."""
        if tool_name in self.tools:
            return self.tools[tool_name].timeout
        return TOOL_REGISTRY.get(tool_name, {}).get("timeout", self.timeout)

    def get_tool_extra_args(self, tool_name: str) -> list:
        """Get extra args for a tool."""
        if tool_name in self.tools:
            extra = self.tools[tool_name].extra_args.strip()
            if extra:
                return extra.split()
        return []


def load_config(args: Any) -> Config:
    """
    Load configuration from yaml file and CLI args.
    Priority: CLI args > yaml file > defaults
    """
    config = Config()

    yaml_data = _find_and_load_yaml(args)
    if yaml_data:
        _apply_yaml(config, yaml_data)

    _apply_args(config, args)

    return config


def _find_and_load_yaml(args: Any) -> Optional[Dict]:
    """Find and load yaml config file."""
    search_paths = []

    if hasattr(args, "config") and args.config:
        search_paths.append(Path(args.config))

    search_paths.extend([
        Path("./easyrecon.yaml"),
        Path.home() / ".easyrecon.yaml",
    ])

    for path in search_paths:
        if path.exists():
            return _load_yaml_file(path)

    return None


def _load_yaml_file(path: Path) -> Optional[Dict]:
    """Load and parse a yaml file."""
    if not YAML_AVAILABLE:
        return None

    try:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        print(f"[!] config.yaml parse error: {e} — using defaults")
        return None
    except OSError:
        return None


def _apply_yaml(config: Config, data: Dict) -> None:
    """Apply yaml data to config object."""
    settings = data.get("settings", {})

    if "output_dir" in settings:
        config.output_dir = Path(settings["output_dir"])
    if "threads" in settings:
        config.threads = int(settings["threads"])
    if "auto_install" in settings:
        config.auto_install = bool(settings["auto_install"])
    if "save_raw" in settings:
        config.save_raw = bool(settings["save_raw"])
    if "default_timeout" in settings:
        config.timeout = int(settings["default_timeout"])

    tools_data = data.get("tools", {})
    for tool_name, tool_settings in tools_data.items():
        if tool_name in config.tools:
            if "enabled" in tool_settings:
                config.tools[tool_name].enabled = bool(tool_settings["enabled"])
            if "timeout" in tool_settings:
                config.tools[tool_name].timeout = int(tool_settings["timeout"])
            if "extra_args" in tool_settings:
                config.tools[tool_name].extra_args = str(tool_settings["extra_args"])


def _apply_args(config: Config, args: Any) -> None:
    """Apply CLI arguments to config."""
    if hasattr(args, "target") and args.target:
        config.target = _normalize_target(args.target)
    if hasattr(args, "output") and args.output:
        config.output_dir = Path(args.output)
    if hasattr(args, "phase") and args.phase:
        config.phase = args.phase
    if hasattr(args, "timeout") and args.timeout:
        config.timeout = args.timeout
        for tool_cfg in config.tools.values():
            tool_cfg.timeout = args.timeout
    if hasattr(args, "no_install") and args.no_install:
        config.no_install = True


def _normalize_target(target: str) -> str:
    """Strip protocol and trailing slashes from target."""
    target = target.strip()
    for prefix in ["https://", "http://", "ftp://"]:
        if target.startswith(prefix):
            target = target[len(prefix):]
    target = target.rstrip("/")
    return target


def check_python_version() -> None:
    """Ensure Python >= 3.8."""
    if sys.version_info < (3, 8):
        print(f"[!] Python 3.8+ required. Current: {sys.version}")
        print("    Install from: https://python.org/downloads/")
        sys.exit(1)
