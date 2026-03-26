#!/usr/bin/env python3
"""
easyrecon — AI-Powered Recon Suite
Fast, automated reconnaissance for bug bounty hunters and pentesters.

Usage:
    easyrecon target.com
    easyrecon target.com --phase subdomain
    easyrecon --help

Author: @unrealsrabon
Version: 1.0.0
"""

import argparse
import re
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Version check before anything else
if sys.version_info < (3, 8):
    print(f"[!] Python 3.8+ required. Current: {sys.version}")
    print("    Install from: https://python.org/downloads/")
    sys.exit(1)

from utils.config import load_config, Config
from utils.checker import check_go, check_all_tools, auto_install_missing
from utils.display import (
    print_banner, print_tool_check_table, print_warning,
    print_error, print_info, print_final_summary, print_interrupt,
    print_success,
)
from modules.subdomains import run_subdomain_phase
from modules.urls import run_url_phase
from modules.live import run_live_phase
from modules.categorize import run_categorize_phase
from modules.report import run_report_phase

VERSION = "1.0.0"

# Global state for interrupt handling
_current_output_dir: Optional[Path] = None
_collected_subdomains = []
_collected_urls = []
_categorized = {}
_start_time = 0.0


def setup_signal_handler() -> None:
    """Setup graceful Ctrl+C handler."""
    def _handler(sig, frame):
        print_interrupt()
        if _current_output_dir and _current_output_dir.exists():
            print_info(f"Partial results saved to: {_current_output_dir}")
        sys.exit(0)
    signal.signal(signal.SIGINT, _handler)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="easyrecon",
        description="Fast automated recon suite for bug bounty hunters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  easyrecon target.com
  easyrecon target.com --phase subdomain
  easyrecon target.com --timeout 60
  easyrecon target.com --output ~/results
  easyrecon target.com --config custom.yaml
  easyrecon target.com --no-install

Phases:
  subdomain   Run subdomain enumeration only
  urls        Run URL discovery only
  live        Run live host detection only
  categorize  Run URL categorization only
  report      Generate report from existing results
        """,
    )

    parser.add_argument(
        "target",
        nargs="?",
        help="Target domain (e.g. target.com)",
    )
    parser.add_argument(
        "--phase",
        choices=["subdomain", "urls", "live", "categorize", "report"],
        help="Run a specific phase only",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="Override timeout for all tools (seconds)",
    )
    parser.add_argument(
        "--output",
        help="Custom output directory",
    )
    parser.add_argument(
        "--config",
        help="Path to custom config.yaml",
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Skip auto-install of missing tools",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"easyrecon v{VERSION}",
    )

    return parser.parse_args()


def validate_target(target: str) -> str:
    """
    Validate and normalize target domain.

    Returns:
        Clean domain string

    Raises:
        SystemExit on invalid target
    """
    if not target:
        print_error("No target specified")
        print_info("Usage: easyrecon target.com")
        sys.exit(1)

    # Strip protocol
    for prefix in ["https://", "http://", "ftp://"]:
        if target.startswith(prefix):
            target = target[len(prefix):]

    target = target.rstrip("/").strip()

    # Validate domain format
    domain_pattern = re.compile(
        r"^(?:[a-zA-Z0-9]"
        r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
        r"[a-zA-Z]{2,}$"
    )
    if not domain_pattern.match(target):
        print_error(f"Invalid target: '{target}'")
        print_info("Provide a valid domain like: target.com or sub.target.com")
        sys.exit(1)

    # Warn about private IPs passed as domain
    private_patterns = ["192.168.", "10.", "172.16.", "localhost", "127.0."]
    for pat in private_patterns:
        if target.startswith(pat):
            print_warning(f"'{target}' looks like an internal address")

    return target


def build_output_dir(target: str, base_dir: Path) -> Path:
    """Build unique output directory path."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    dir_name = f"{target}_{timestamp}"
    output_dir = base_dir / dir_name

    # Avoid overwrite
    counter = 1
    original = output_dir
    while output_dir.exists():
        output_dir = Path(f"{original}_{counter}")
        counter += 1

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print_error(f"Cannot create output directory: {e}")
        print_info("Try: --output /tmp/easyrecon or check permissions")
        sys.exit(1)

    return output_dir


def run_dependency_check(config: Config) -> None:
    """Check and install tools, display status table."""
    if not check_go():
        print_error("Go is not installed — required for tool installation")
        print_info("Install Go from: https://go.dev/dl/")
        print_info("Then run easyrecon again")
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
    """Main entry point."""
    global _current_output_dir, _collected_subdomains, _collected_urls
    global _categorized, _start_time

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

    errors_log = output_dir / "errors.log"

    print_banner(
        target=target,
        output_dir=str(output_dir),
        mode=f"Phase: {config.phase.capitalize()}" if config.phase else "Full Recon",
    )

    run_dependency_check(config)

    _start_time = time.time()

    subdomains: list = []
    urls: list = []
    live_subs: list = []
    live_urls: list = []
    categorized: dict = {}

    phase = config.phase

    try:
        # Phase 1 — Subdomain Enumeration
        if not phase or phase == "subdomain":
            subdomains, ok = run_subdomain_phase(target, config, output_dir)
            _collected_subdomains = subdomains
            if not ok and not phase:
                print_warning("Subdomain phase failed — continuing with empty subdomain list")

        # Phase 2 — URL Discovery
        if not phase or phase == "urls":
            urls, ok = run_url_phase(target, config, output_dir)
            _collected_urls = urls
            if not ok and not phase:
                print_warning("URL phase failed — continuing without URL data")

        # Phase 3+4 — Live Detection
        if not phase or phase == "live":
            if not subdomains and not urls:
                print_warning("No data for live phase — skipping")
            else:
                live_subs, live_urls, ok = run_live_phase(
                    subdomains=subdomains,
                    urls=urls,
                    config=config,
                    output_dir=output_dir,
                )
                if not ok and not phase:
                    print_warning("Live phase skipped — using raw data for categorization")
                    live_urls = urls

        # Phase 5 — Categorization
        if not phase or phase == "categorize":
            urls_to_categorize = live_urls if live_urls else urls
            if not urls_to_categorize:
                print_warning("No URLs to categorize — skipping")
                categorized = {}
            else:
                categorized = run_categorize_phase(
                    urls=urls_to_categorize,
                    config=config,
                    output_dir=output_dir,
                )
            _categorized = categorized

        # Phase 6 — Report
        if not phase or phase == "report":
            duration = time.time() - _start_time
            run_report_phase(
                target=target,
                config=config,
                output_dir=output_dir,
                subdomains_total=len(subdomains),
                subdomains_live=live_subs,
                urls_total=len(urls),
                urls_live=live_urls,
                categorized=categorized,
                duration=duration,
            )

    except KeyboardInterrupt:
        print_interrupt()
        print_info(f"Partial results saved to: {output_dir}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        try:
            with open(errors_log, "a") as f:
                import traceback
                f.write(f"\n[{datetime.now()}] {e}\n{traceback.format_exc()}\n")
        except Exception:
            pass
        sys.exit(1)

    # Final Summary
    duration = time.time() - _start_time
    print_final_summary(
        target=target,
        duration=duration,
        subdomain_total=len(subdomains),
        subdomain_live=len(live_subs),
        url_total=len(urls),
        url_live=len(live_urls),
        categorized=categorized,
        output_dir=str(output_dir),
    )


if __name__ == "__main__":
    main()
