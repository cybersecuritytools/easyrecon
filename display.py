"""
easyrecon Display System
All Rich UI components for premium terminal experience.
"""

import time
from typing import Dict, List, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.rule import Rule
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.live import Live
    from rich.layout import Layout
    from rich.align import Align
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    import pyfiglet
    PYFIGLET_AVAILABLE = True
except ImportError:
    PYFIGLET_AVAILABLE = False

VERSION = "1.0.4"

console = Console(color_system="256", force_terminal=True, force_interactive=True) if RICH_AVAILABLE else None

PHASE_COLORS = {
    "subdomain": "cyan",
    "urls": "yellow",
    "live": "green",
    "categorize": "magenta",
    "report": "blue",
}

PHASE_DESCRIPTIONS = {
    "subdomain": "Hunting subdomains across 3 engines...",
    "urls": "Discovering URLs from historical and live sources...",
    "live": "Probing live hosts and filtering active URLs...",
    "categorize": "Mapping attack surface by category...",
    "report": "Generating your recon report...",
}

STATUS_ICONS = {
    "success": "[bold green]✅[/bold green]",
    "empty": "[bold yellow]⚠️ [/bold yellow]",
    "timeout": "[bold yellow]⏱️ [/bold yellow]",
    "error": "[bold red]⚠️ [/bold red]",
    "missing": "[bold red]❌[/bold red]",
    "install_failed": "[bold red]❌[/bold red]",
    "disabled": "[bold dim]⏭️ [/bold dim]",
    "installing": "[bold blue]⬇️ [/bold blue]",
    "installed_now": "[bold green]✅[/bold green]",
    "skipped": "[bold dim]⏭️ [/bold dim]",
}


def print_banner(target: str, output_dir: str, mode: str = "Full Recon") -> None:
    """Print the easyrecon launch banner."""
    if not RICH_AVAILABLE:
        print(f"\n=== easyrecon v{VERSION} ===\nTarget: {target}\n")
        return

    if PYFIGLET_AVAILABLE:
        try:
            art = pyfiglet.figlet_format("easyrecon", font="slant")
        except Exception:
            art = "  easyrecon"
    else:
        art = (
            "   ___  ____ ________  __________  _________  ____ \n"
            "  / _ \\/ __ `/ ___/ / / / ___/ _ \\/ ___/ __ \\/ __ \\\n"
            " /  __/ /_/ (__  ) /_/ / /  /  __/ /__/ /_/ / / / /\n"
            " \\___/\\__,_/____/\\__, /_/   \\___/\\___/\\____/_/ /_/ \n"
            "                /____/                             \n"
        )
    console.print(f"[bold red]{art}[/bold red]")
    console.print(
        Panel.fit(
            f"[bold white]Target[/bold white]   → [cyan]{target}[/cyan]\n"
            f"[bold white]Mode[/bold white]     → [green]{mode}[/green]\n"
            f"[bold white]Output[/bold white]   → [dim]{output_dir}[/dim]\n"
            f"[bold white]Version[/bold white]  → [dim]v{VERSION}[/dim]",
            border_style="dim",
            padding=(0, 2),
        )
    )
    console.print()


def print_phase_header(phase: str) -> None:
    """Print a phase separator header."""
    if not RICH_AVAILABLE:
        print(f"\n--- Phase: {phase.upper()} ---")
        return

    color = PHASE_COLORS.get(phase, "white")
    desc = PHASE_DESCRIPTIONS.get(phase, "")
    phase_num = {
        "subdomain": 1, "urls": 2, "live": 3,
        "categorize": 4, "report": 5,
    }.get(phase, 0)

    console.print()
    console.print(Rule(f"[bold {color}] Phase {phase_num} — {phase.upper()} [/bold {color}]", style=color))
    if desc:
        console.print(f"  [dim]{desc}[/dim]")
    console.print()


from contextlib import contextmanager

def get_spinner_message(tools: List[str], target_type: str, target: str) -> str:
    """Generate dynamic grammar and contextual sentences for the loading spinner."""
    tools_str = ", ".join(tools)
    verb = "is" if len(tools) == 1 else "are"
    
    if target_type == "subdomains":
        return f"[cyan][bold]{tools_str}[/bold] {verb} running to find out every possible subdomain of [bold]{target}[/bold]...[/cyan]"
    elif target_type == "urls":
        return f"[cyan][bold]{tools_str}[/bold] {verb} running to find out every possible url of [bold]{target}[/bold]...[/cyan]"
    elif target_type == "live_subdomains":
        return f"[cyan][bold]{tools_str}[/bold] {verb} probing the discovered subdomains of [bold]{target}[/bold] to find live web servers...[/cyan]"
    elif target_type == "live_urls":
        return f"[cyan][bold]{tools_str}[/bold] {verb} validating the discovered URLs of [bold]{target}[/bold] to sort out active endpoints...[/cyan]"
    
    return f"[cyan][bold]{tools_str}[/bold] {verb} running on [bold]{target}[/bold]...[/cyan]"

@contextmanager
def print_live_tools_spinner(tools: List[str], target_type: str = "targets", target: str = ""):
    """Display a live spinner while tools are running in the background."""
    if not RICH_AVAILABLE or not tools:
        yield None
        return

    status_msg = get_spinner_message(tools, target_type, target)
    with console.status(status_msg, spinner="dots", speed=1.0) as status:
        status.update(status_msg)  # Force immediate render on main thread
        yield status
def print_tool_result(
    tool_name: str,
    status: str,
    count: int = 0,
    elapsed: float = 0.0,
    message: str = "",
) -> None:
    """Print a single tool result line."""
    if not RICH_AVAILABLE:
        icon = "✅" if status == "success" else "❌"
        print(f"  {icon} {tool_name:<16} {count} found  [{elapsed:.1f}s]")
        return

    icon = STATUS_ICONS.get(status, "  ")
    name_str = f"[bold]{tool_name:<16}[/bold]"

    if status == "success":
        result_str = f"[green]{count} found[/green]    [dim][{elapsed:.1f}s][/dim]"
    elif status == "empty":
        result_str = f"[yellow]0 results[/yellow]    [dim][{elapsed:.1f}s][/dim]"
    elif status == "timeout":
        timeout_msg = message or "timeout hit"
        result_str = f"[yellow]{timeout_msg}[/yellow]  [dim][{elapsed:.1f}s][/dim]"
    elif status in ("missing", "install_failed"):
        result_str = f"[red]{message}[/red]"
    elif status == "disabled":
        result_str = "[dim]disabled in config[/dim]"
    elif status == "installing":
        result_str = f"[blue]{message}[/blue]"
    elif status == "installed_now":
        result_str = f"[green]installed — {count} found[/green]  [dim][{elapsed:.1f}s][/dim]"
    else:
        result_str = f"[dim]{message or status}[/dim]"

    console.print(f"  {icon} {name_str} {result_str}")


def print_tool_check_table(statuses: Dict[str, str]) -> None:
    """Print dependency check table."""
    if not RICH_AVAILABLE:
        for tool, status in statuses.items():
            icon = "✅" if status in ("installed", "installed_now") else "❌"
            print(f"  {icon} {tool}: {status}")
        return

    table = Table(
        show_header=True,
        header_style="bold dim",
        box=box.SIMPLE,
        padding=(0, 1),
    )
    table.add_column("Tool", style="bold", width=16)
    table.add_column("Status", width=20)
    table.add_column("Action", style="dim")

    for tool_name, status in statuses.items():
        if status == "installed":
            status_str = "[green]✅ installed[/green]"
            action = "—"
        elif status == "installed_now":
            status_str = "[green]✅ installed now[/green]"
            action = "—"
        elif status == "missing":
            status_str = "[red]❌ missing[/red]"
            install_cmd = TOOL_REGISTRY_REF.get(tool_name, {}).get("install_cmd", "")
            action = f"go install ..."
        elif status == "install_failed":
            status_str = "[red]❌ install failed[/red]"
            action = "install manually"
        elif status == "disabled":
            status_str = "[dim]⏭️  disabled[/dim]"
            action = "enable in config.yaml"
        else:
            status_str = f"[dim]{status}[/dim]"
            action = "—"

        table.add_row(tool_name, status_str, action)

    console.print(table)


def print_live_subdomain(host: str, status_code: str, title: str, server: str, tech: str) -> None:
    """Print a single live host result."""
    if not RICH_AVAILABLE:
        print(f"  {status_code}  {host}  {title}")
        return

    code_color = {
        "200": "green",
        "301": "yellow",
        "302": "yellow",
        "403": "red",
        "401": "red",
        "405": "yellow",
    }.get(status_code, "dim")

    console.print(
        f"  [{code_color}]{status_code}[/{code_color}]  "
        f"[bold]{host:<40}[/bold]  "
        f"[dim]{title[:30]:<30}[/dim]  "
        f"[blue]{server[:20]:<20}[/blue]  "
        f"[dim]{tech[:20]}[/dim]"
    )


def print_category_bars(categorized: Dict[str, List[str]]) -> None:
    """Print category results as visual bar chart."""
    if not RICH_AVAILABLE:
        for cat, items in categorized.items():
            print(f"  {cat:<12} {len(items)}")
        return

    from utils.registry import CATEGORY_PRIORITY

    console.print()
    max_count = max((len(v) for v in categorized.values()), default=1)
    bar_width = 20

    ordered = []
    for cat in CATEGORY_PRIORITY:
        if cat in categorized and categorized[cat]:
            ordered.append(cat)
    for cat in categorized:
        if cat not in ordered and categorized[cat]:
            ordered.append(cat)

    for cat in ordered:
        count = len(categorized[cat])
        if count == 0:
            continue
        filled = int((count / max_count) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)

        priority_colors = {
            "sensitive": "red",
            "admin": "yellow",
            "login": "yellow",
            "upload": "yellow",
            "api": "cyan",
            "params": "blue",
        }
        color = priority_colors.get(cat, "dim")

        console.print(
            f"  [{color}]{cat:<12}[/{color}]  "
            f"[{color}]{bar}[/{color}]  "
            f"[bold]{count:>5}[/bold]"
        )
    console.print()


def print_final_summary(
    target: str,
    duration: float,
    subdomain_total: int,
    subdomain_live: int,
    url_total: int,
    url_live: int,
    categorized: Dict[str, List[str]],
    output_dir: str,
) -> None:
    """Print the final recon complete summary panel."""
    if not RICH_AVAILABLE:
        print(f"\n=== RECON COMPLETE ===")
        print(f"Target: {target}")
        print(f"Duration: {_format_duration(duration)}")
        return

    mins = int(duration // 60)
    secs = int(duration % 60)
    duration_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"

    cat_lines = []
    from utils.registry import CATEGORY_PRIORITY
    for cat in CATEGORY_PRIORITY:
        count = len(categorized.get(cat, []))
        if count > 0:
            cat_lines.append(f"  [dim]{cat:<12}[/dim] [bold]{count}[/bold]")

    cat_text = "\n".join(cat_lines) if cat_lines else "  [dim]no findings[/dim]"

    content = (
        f"[bold green]RECON COMPLETE[/bold green]\n\n"
        f"[bold]Target[/bold]      →  [cyan]{target}[/cyan]\n"
        f"[bold]Duration[/bold]    →  [green]{duration_str}[/green]\n"
        f"[bold]Subdomains[/bold]  →  {subdomain_total} found  /  [green]{subdomain_live} live[/green]\n"
        f"[bold]URLs[/bold]        →  {url_total} found  /  [green]{url_live} live[/green]\n\n"
        f"[bold dim]Attack Surface:[/bold dim]\n"
        f"{cat_text}\n\n"
        f"[bold]Output[/bold]  →  [dim]{output_dir}[/dim]"
    )

    console.print()
    console.print(Panel(content, border_style="green", padding=(1, 3)))
    console.print()


def print_warning(message: str) -> None:
    """Print a warning message."""
    if RICH_AVAILABLE:
        console.print(f"  [bold yellow]⚠️  {message}[/bold yellow]")
    else:
        print(f"  [!] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    if RICH_AVAILABLE:
        console.print(f"  [bold red]❌  {message}[/bold red]")
    else:
        print(f"  [ERROR] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    if RICH_AVAILABLE:
        console.print(f"  [dim]→  {message}[/dim]")
    else:
        print(f"  -> {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    if RICH_AVAILABLE:
        console.print(f"  [bold green]✅  {message}[/bold green]")
    else:
        print(f"  [+] {message}")


def print_counter(label: str, count: int) -> None:
    """Print a running counter."""
    if RICH_AVAILABLE:
        console.print(f"  [dim]{label}:[/dim] [bold cyan]{count}[/bold cyan]")
    else:
        print(f"  {label}: {count}")


def print_phase_skip(phase: str, reason: str) -> None:
    """Print phase skipped message."""
    if RICH_AVAILABLE:
        console.print(f"  [bold dim]✖️   Phase {phase} skipped — {reason}[/bold dim]")
    else:
        print(f"  [SKIP] Phase {phase}: {reason}")


def print_interrupt() -> None:
    """Print keyboard interrupt message."""
    if RICH_AVAILABLE:
        console.print("\n\n  [bold yellow]⚡  Interrupted! Saving collected results...[/bold yellow]")
    else:
        print("\n\n  [!] Interrupted! Saving results...")


def _format_duration(seconds: float) -> str:
    """Format duration as human readable string."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}m {secs}s" if mins > 0 else f"{secs}s"


try:
    from utils.registry import TOOL_REGISTRY as TOOL_REGISTRY_REF
except ImportError:
    TOOL_REGISTRY_REF = {}
