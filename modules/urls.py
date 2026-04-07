"""
easyrecon Phase 2 — URL Discovery
Runs gau, waybackurls, katana in parallel.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple

from utils.config import Config
from utils.runner import run_tool, ToolResult, CriticalToolMissing
from utils.merger import merge_urls, save_to_file
from utils.display import (
    print_phase_header, print_tool_result, print_live_tools_spinner,
    print_warning, print_counter, print_phase_skip, get_spinner_message,
)
from utils.registry import PHASE_TOOLS


def run_url_phase(
    target: str,
    config: Config,
    output_dir: Path,
) -> Tuple[List[str], bool]:
    """
    Run Phase 2: URL discovery.

    Args:
        target: Target domain
        config: Config object
        output_dir: Base output directory

    Returns:
        (list of URLs, success bool)
    """
    print_phase_header("urls")

    raw_dir = output_dir / "raw"
    processed_dir = output_dir / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    tools = PHASE_TOOLS["urls"]
    enabled_tools = [t for t in tools if config.is_tool_enabled(t)]

    if not enabled_tools:
        print_phase_skip("urls", "all URL tools disabled in config")
        return [], False

    results: Dict[str, List[str]] = {}
    active_tools = enabled_tools.copy()

    import time
    with print_live_tools_spinner(active_tools, "urls", target) as status:
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
                            status.update(f"[cyan][bold]{', '.join(active_tools)}[/bold] are running to find out every possible urls on the internet...[/cyan]")
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
                    print_phase_skip("urls", str(e))
                    return [], False
                except Exception as e:
                    print_warning(f"{tool_name} unexpected error: {e}")
                    results[tool_name] = []
                    if tool_name in active_tools:
                        active_tools.remove(tool_name)
                    if status:
                        if active_tools:
                            status.update(f"[cyan][bold]{', '.join(active_tools)}[/bold] are running to find out every possible urls on the internet...[/cyan]")
                        else:
                            status.update("[cyan]Finalizing...[/cyan]")

    all_urls = merge_urls(results)

    if not all_urls:
        print_warning("No URLs discovered — target may have no historical data")
        return [], False

    save_to_file(all_urls, processed_dir / "all_urls.txt")
    print_counter("Total unique URLs", len(all_urls))

    if len(all_urls) > 10000:
        print_warning(f"Large result set ({len(all_urls)} URLs) — processing in batches")

    return all_urls, True
