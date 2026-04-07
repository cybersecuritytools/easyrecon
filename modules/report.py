"""
easyrecon Phase 6 — Report Generation
Generates clean, professional report.md
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List

from utils.config import Config
from utils.display import print_phase_header, print_success
from modules.categorize import get_top_findings, NEXT_STEPS
from utils.registry import CATEGORY_PRIORITY


def run_report_phase(
    target: str,
    config: Config,
    output_dir: Path,
    subdomains_total: int,
    subdomains_live: List[str],
    urls_total: int,
    urls_live: List[str],
    categorized: Dict[str, List[str]],
    duration: float,
) -> Path:
    """
    Run Phase 6: Report generation.

    Returns:
        Path to generated report.md
    """
    print_phase_header("report")

    report_path = output_dir / "report.md"
    content = _build_report(
        target=target,
        output_dir=output_dir,
        subdomains_total=subdomains_total,
        subdomains_live=subdomains_live,
        urls_total=urls_total,
        urls_live=urls_live,
        categorized=categorized,
        duration=duration,
    )

    try:
        report_path.write_text(content)
        print_success(f"Report saved → {report_path}")
    except OSError as e:
        from utils.display import print_error
        print_error(f"Could not write report: {e}")

    return report_path


def _build_report(
    target: str,
    output_dir: Path,
    subdomains_total: int,
    subdomains_live: List[str],
    urls_total: int,
    urls_live: List[str],
    categorized: Dict[str, List[str]],
    duration: float,
) -> str:
    """Build the full markdown report content."""

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mins = int(duration // 60)
    secs = int(duration % 60)
    duration_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
    total_findings = sum(len(v) for v in categorized.values())

    lines = []

    # Header
    lines += [
        "# easyrecon Report",
        "",
        f"| | |",
        f"|---|---|",
        f"| **Target** | `{target}` |",
        f"| **Date** | {now} |",
        f"| **Duration** | {duration_str} |",
        f"| **Output** | `{output_dir}` |",
        "",
        "---",
        "",
    ]

    # Summary Table
    lines += [
        "## Summary",
        "",
        "| Phase | Result |",
        "|---|---|",
        f"| Subdomains Found | {subdomains_total} |",
        f"| Live Subdomains | {len(subdomains_live)} |",
        f"| URLs Found | {urls_total} |",
        f"| Live URLs | {len(urls_live)} |",
        f"| Total Categorized | {total_findings} |",
        "",
        "---",
        "",
    ]

    # Attack Surface Map
    lines += [
        "## Attack Surface Map",
        "",
        "| Category | Count | Priority |",
        "|---|---|---|",
    ]

    priority_labels = {
        "sensitive": "🔴 HIGH",
        "admin": "🟠 HIGH",
        "login": "🟠 HIGH",
        "upload": "🟡 MEDIUM",
        "api": "🟡 MEDIUM",
        "params": "🔵 MEDIUM",
        "backup": "🟡 MEDIUM",
        "errors": "⚪ INFO",
        "php": "⚪ INFO",
        "js": "⚪ INFO",
        "json": "⚪ INFO",
        "xml": "⚪ INFO",
    }

    for cat in CATEGORY_PRIORITY:
        count = len(categorized.get(cat, []))
        if count > 0:
            priority = priority_labels.get(cat, "⚪ INFO")
            lines.append(f"| {cat} | {count} | {priority} |")

    lines += ["", "---", ""]

    # Top 10 Interesting Findings
    top = get_top_findings(categorized, limit=10)
    if top:
        lines += [
            "## Top 10 Most Interesting Findings",
            "",
            "| # | Category | URL/Host |",
            "|---|---|---|",
        ]
        for i, finding in enumerate(top, 1):
            lines.append(f"| {i} | `{finding['category']}` | `{finding['url']}` |")
        lines += ["", "---", ""]

    # Live Subdomains
    if subdomains_live:
        lines += [
            "## Live Subdomains",
            "",
            "```",
        ]
        for sub in subdomains_live[:100]:
            lines.append(sub)
        if len(subdomains_live) > 100:
            lines.append(f"... and {len(subdomains_live) - 100} more (see live_subdomains.txt)")
        lines += ["```", "", "---", ""]

    # Category Details
    lines += ["## Category Details", ""]

    for cat in CATEGORY_PRIORITY:
        items = categorized.get(cat, [])
        if not items:
            continue

        lines += [
            f"### {cat.capitalize()} ({len(items)})",
            "",
            "<details>",
            f"<summary>View all {len(items)} {cat} findings</summary>",
            "",
            "```",
        ]
        for item in items[:200]:
            lines.append(item)
        if len(items) > 200:
            lines.append(f"... {len(items) - 200} more in categorized/{cat}.txt")
        lines += ["```", "", "</details>", ""]

        # Next steps for high priority categories
        if cat in NEXT_STEPS:
            lines += [f"**Suggested next steps for {cat}:**", ""]
            for step in NEXT_STEPS[cat]:
                lines.append(f"- {step}")
            lines.append("")

    lines += ["---", ""]

    # Footer
    lines += [
        "## Notes",
        "",
        "- This report was generated by [easyrecon](https://github.com/unrealsrabon/easyrecon)",
        "- All findings are passive/active recon only — no exploitation",
        "- Always ensure you have written permission before testing",
        f"- Full results available in: `{output_dir}`",
        "",
        f"*Generated by easyrecon v1.7 — {now}*",
    ]

    return "\n".join(lines)
