#!/usr/bin/env python3
"""
easyrecon — AI-Powered Recon Suite
Fast, automated reconnaissance for bug bounty hunters and pentesters.
"""

import argparse
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

if sys.version_info < (3, 8):
	print(f"[!] Python 3.8+ required. Current: {sys.version}")
	print("    Install from: https://python.org/downloads/")
	sys.exit(1)

# Prioritize Go binaries so we don't accidentally run system binaries that might require sudo (like Kali's amass)
try:
    _go_env = subprocess.run(["go", "env", "GOPATH"], capture_output=True, text=True, timeout=2)
    _go_bin = Path(_go_env.stdout.strip()) / "bin" if _go_env.stdout.strip() else Path.home() / "go" / "bin"
except Exception:
    _go_bin = Path.home() / "go" / "bin"
os.environ["PATH"] = f"{_go_bin}{os.pathsep}{os.environ.get('PATH', '')}"

from utils.config import Config, load_config
from utils.checker import auto_install_missing, check_all_tools, check_go
from utils.display import (
	print_banner,
	print_error,
	print_final_summary,
	print_info,
	print_interrupt,
	print_tool_check_table,
	print_warning,
)
from modules.subdomains import run_subdomain_phase
from modules.urls import run_url_phase
from modules.live import run_live_phase
from modules.categorize import run_categorize_phase
from modules.report import run_report_phase

VERSION = "1.7"

_current_output_dir: Optional[Path] = None
_collected_subdomains: List[str] = []
_collected_urls: List[str] = []
_categorized: Dict[str, List[str]] = {}


def setup_signal_handler() -> None:
	"""Setup graceful Ctrl+C handler."""

	def _handler(sig, frame):
		print_interrupt()
		if _current_output_dir and _current_output_dir.exists():
			print_info(f"Partial results saved to: {_current_output_dir}")
		import os
		os._exit(1)

	signal.signal(signal.SIGINT, _handler)


def parse_args() -> argparse.Namespace:
	"""Parse CLI arguments."""
	parser = argparse.ArgumentParser(
		prog="easyrecon",
		description="Fast automated recon suite for bug bounty hunters",
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	parser.add_argument("target", nargs="?", help="Target domain (e.g. target.com)")
	parser.add_argument(
		"--phase",
		choices=["subdomain", "urls", "live", "categorize", "report"],
		help="Run a specific phase only",
	)
	parser.add_argument("--timeout", type=int, help="Override timeout for all tools")
	parser.add_argument(
		"-nt",
		"--no-timeout",
		action="store_true",
		help="Disable process timeout for this run",
	)
	parser.add_argument("--output", help="Custom output directory")
	parser.add_argument("--config", help="Path to custom config.yaml")
	parser.add_argument("--no-install", action="store_true", help="Skip auto-install")
	parser.add_argument("--version", action="version", version=f"easyrecon v{VERSION}")
	return parser.parse_args()


def validate_target(target: str) -> str:
	"""Validate and normalize target domain."""
	if not target:
		print_error("No target specified")
		print_info("Usage: easyrecon target.com")
		sys.exit(1)

	for prefix in ["https://", "http://", "ftp://"]:
		if target.startswith(prefix):
			target = target[len(prefix):]

	target = target.rstrip("/").strip()

	domain_pattern = re.compile(
		r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
	)
	if not domain_pattern.match(target):
		print_error(f"Invalid target: '{target}'")
		print_info("Provide a valid domain like: target.com or sub.target.com")
		sys.exit(1)

	return target


def build_output_dir(target: str, base_dir: Path) -> Path:
	"""Build unique output directory path."""
	timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
	output_dir = base_dir / f"{target}_{timestamp}"

	counter = 1
	original = output_dir
	while output_dir.exists():
		output_dir = Path(f"{original}_{counter}")
		counter += 1

	output_dir.mkdir(parents=True, exist_ok=True)
	return output_dir


def run_dependency_check(config: Config) -> None:
	"""Check and install tools, then display status table."""
	if not check_go():
		print_error("Go is not installed — required for tool installation")
		print_info("Install Go from: https://go.dev/dl/")
		sys.exit(1)

	if not config.no_install and config.auto_install:
		statuses = auto_install_missing(
			config=config,
			display_callback=lambda name, status, msg: print_info(f"{name}: {msg}"),
		)
	else:
		statuses = check_all_tools(config)

	print_tool_check_table(statuses)


def main() -> None:
	"""Main entrypoint."""
	global _current_output_dir, _collected_subdomains, _collected_urls, _categorized

	setup_signal_handler()
	args = parse_args()

	if not args.target:
		print_error("No target specified")
		print_info("Usage: easyrecon target.com")
		print_info("       easyrecon --help")
		sys.exit(1)

	target = validate_target(args.target)
	config = load_config(args)
	config.target = target

	output_dir = build_output_dir(target, config.output_dir)
	_current_output_dir = output_dir

	print_banner(
		target=target,
		output_dir=str(output_dir),
		mode=f"Phase: {config.phase.capitalize()}" if config.phase else "Full Recon",
	)

	run_dependency_check(config)
	start_time = time.time()

	phase = config.phase
	subdomains: List[str] = []
	urls: List[str] = []
	live_subdomains: List[str] = []
	live_urls: List[str] = []
	categorized: Dict[str, List[str]] = {}

	try:
		if not phase or phase == "subdomain":
			subdomains, ok = run_subdomain_phase(target, config, output_dir)
			_collected_subdomains = subdomains
			if not ok and not phase:
				print_warning("Subdomain phase failed — continuing")

		if not phase or phase == "urls":
			urls, ok = run_url_phase(target, config, output_dir)
			_collected_urls = urls
			if not ok and not phase:
				print_warning("URL phase failed — continuing")

		if not phase or phase == "live":
			live_subdomains, live_urls, _ = run_live_phase(subdomains, urls, config, output_dir, target)

		if not phase or phase == "categorize":
			source_urls = live_urls if live_urls else urls
			categorized = run_categorize_phase(source_urls, config, output_dir)
			_categorized = categorized

		if not phase or phase == "report":
			run_report_phase(
				target=target,
				config=config,
				output_dir=output_dir,
				subdomains_total=len(subdomains),
				subdomains_live=live_subdomains,
				urls_total=len(urls),
				urls_live=live_urls,
				categorized=categorized,
				duration=time.time() - start_time,
			)

		print_final_summary(
			target=target,
			duration=time.time() - start_time,
			subdomain_total=len(subdomains),
			subdomain_live=len(live_subdomains),
			url_total=len(urls),
			url_live=len(live_urls),
			categorized=categorized,
			output_dir=str(output_dir),
		)

	except KeyboardInterrupt:
		print_interrupt()
	except Exception as e:
		print_error(f"Unexpected error: {e}")
		if _current_output_dir:
			print_info(f"Partial output path: {_current_output_dir}")
		sys.exit(1)


if __name__ == "__main__":
	main()
