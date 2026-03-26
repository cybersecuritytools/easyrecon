"""
easyrecon Phase 5 — Smart Categorization
Pattern-based URL categorization into attack surface buckets.
"""

from pathlib import Path
from typing import Dict, List

from utils.config import Config
from utils.merger import save_to_file
from utils.display import print_phase_header, print_category_bars, print_counter
from utils.registry import CATEGORY_PATTERNS, CATEGORY_PRIORITY


def run_categorize_phase(
    urls: List[str],
    config: Config,
    output_dir: Path,
) -> Dict[str, List[str]]:
    """
    Run Phase 5: Smart URL categorization.

    Args:
        urls: List of URLs to categorize
        config: Config object
        output_dir: Base output directory

    Returns:
        Dict of category → list of URLs
    """
    print_phase_header("categorize")

    categorized_dir = output_dir / "categorized"
    categorized_dir.mkdir(parents=True, exist_ok=True)

    categorized: Dict[str, List[str]] = {cat: [] for cat in CATEGORY_PATTERNS}
    categorized["errors"] = []

    if not urls:
        return categorized

    total = len(urls)
    if total > 10000:
        from utils.display import print_warning
        print_warning(f"Large URL set ({total}) — categorizing in batches")

    for url in urls:
        url_lower = url.lower()
        _categorize_url(url, url_lower, categorized)

    for category, items in categorized.items():
        if items:
            unique = sorted(set(items))
            categorized[category] = unique
            save_to_file(unique, categorized_dir / f"{category}.txt")

    total_categorized = sum(len(v) for v in categorized.values())
    print_counter("Total categorized findings", total_categorized)

    print_category_bars(categorized)

    return categorized


def _categorize_url(url: str, url_lower: str, categorized: Dict[str, List[str]]) -> None:
    """
    Categorize a single URL into all matching buckets.
    A URL can belong to multiple categories.
    """
    # Check error status codes (from httpx output format)
    for error_code in ["[403]", "[401]", "[405]"]:
        if error_code in url:
            categorized["errors"].append(url)
            break

    # Check each pattern category
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if pattern in url_lower:
                categorized[category].append(url)
                break


def get_top_findings(
    categorized: Dict[str, List[str]],
    limit: int = 10,
) -> List[Dict]:
    """
    Get top N most interesting findings by priority.

    Returns:
        List of dicts with category and url
    """
    findings = []

    for category in CATEGORY_PRIORITY:
        items = categorized.get(category, [])
        for url in items:
            findings.append({"category": category, "url": url})
            if len(findings) >= limit:
                return findings

    return findings


NEXT_STEPS = {
    "sensitive": [
        "Check /.git for source code exposure (git-dumper)",
        "Try to access /.env for credentials",
        "Test /backup files for sensitive data",
        "Check /config endpoints for database credentials",
    ],
    "admin": [
        "Try default credentials on admin panels",
        "Test for authentication bypass",
        "Check for IDOR in admin functions",
        "Look for exposed admin APIs",
    ],
    "login": [
        "Test for SQL injection in login forms",
        "Try password spraying with common passwords",
        "Check for account enumeration",
        "Test OAuth/SAML misconfiguration",
    ],
    "upload": [
        "Test for unrestricted file upload",
        "Try uploading PHP/ASP shells",
        "Check for path traversal in file parameters",
        "Test MIME type validation bypass",
    ],
    "api": [
        "Check Swagger/OpenAPI docs for exposed endpoints",
        "Test for IDOR in API endpoints",
        "Try GraphQL introspection",
        "Check for missing authentication on API routes",
    ],
    "params": [
        "Test all parameters for XSS",
        "Check redirect parameters for open redirect",
        "Test file/path params for LFI/RFI",
        "Try SQL injection on id/search params",
    ],
}
