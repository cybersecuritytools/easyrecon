"""
easyrecon Phase 1 — Subdomain Enumeration
Runs subfinder, amass, assetfinder in parallel.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple

from utils.config import Config
from utils.runner import run_tool, ToolResult, CriticalToolMissing
from utils.merger import merge_and_dedupe, save_to_file, filter_subdomains_for_target
from utils.display import (
    print_phase_header, print_tool_result, print_live_tools_spinner,
    print_warning, print_counter, print_phase_skip, get_spinner_message,
)
from utils.registry import PHASE_TOOLS


def run_subdomain_phase(
    target: str,
    config: Config,
    output_dir: Path,
) -> Tuple[List[str], bool]:
    """
    Run Phase 1: Subdomain enumeration.

    Args:
        target: Target domain
        config: Config object
        output_dir: Base output directory

    Returns:
        (list of subdomains, success bool)
    """
    print_phase_header("subdomain")

    raw_dir = output_dir / "raw"
    processed_dir = output_dir / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    tools = PHASE_TOOLS["subdomain"]
    enabled_tools = [t for t in tools if config.is_tool_enabled(t)]

    if not enabled_tools:
        print_phase_skip("subdomain", "all tools disabled in config")
        return [], False

    results: Dict[str, List[str]] = {}
    active_tools = enabled_tools.copy()

    with print_live_tools_spinner(active_tools, "subdomains", target) as status:
        time.sleep(0.1)  # Allow UI thread to paint initial animation
        with ThreadPoolExecutor(max_workers=len(enabled_tools)) as executor:
            futures = {
                executor.submit(run_tool, tool_name, target, config): tool_name
                for tool_name in enabled_tools
            }
    
            for future in as_completed(futures):
                tool_name = futures[future]
                
                try:
                    result: ToolResult = future.result()
                    results[tool_name] = result.lines
    
                    # Update state BEFORE printing tool result so spinner correctly reflects remaining tools
                    active_tools.remove(tool_name)
                    if status:
                        if active_tools:
                            status.update(f"[cyan][bold]{', '.join(active_tools)}[/bold] are running to find out every possible subdomains on the internet...[/cyan]")
                        else:
                            status.update("[cyan]Finalizing...[/cyan]")
    
                    print_tool_result(
                        tool_name=tool_name,
                        status=result.status,
                        count=result.count,
                        elapsed=result.elapsed,
                        message=result.message,
                    )
    
                    if config.save_raw and result.lines:
                        save_to_file(result.lines, raw_dir / f"{tool_name}.txt")
    
                except CriticalToolMissing as e:
                    print_phase_skip("subdomain", str(e))
                    return [], False
                except Exception as e:
                    print_warning(f"{tool_name} unexpected error: {e}")
                    results[tool_name] = []
                    if tool_name in active_tools:
                        active_tools.remove(tool_name)
                    if status:
                        if active_tools:
                            status.update(f"[cyan][bold]{', '.join(active_tools)}[/bold] are running to find out every possible subdomains on the internet...[/cyan]")
                        else:
                            status.update("[cyan]Finalizing...[/cyan]")

    all_subs = merge_and_dedupe(results)
    filtered = filter_subdomains_for_target(all_subs, target)

    if not filtered:
        print_warning("No subdomains found — target may block passive recon")
        return [], False

    save_to_file(filtered, processed_dir / "all_subdomains.txt")
    print_counter("Total unique subdomains", len(filtered))

    if len(filtered) > 10000:
        print_warning(f"Large result set ({len(filtered)} subdomains) — processing in batches")

    return filtered, True
