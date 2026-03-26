"""
easyrecon Merger & Deduplication
Merges multiple tool outputs into clean master lists.
"""

import re
from pathlib import Path
from typing import List, Dict, Set


def merge_and_dedupe(results: Dict[str, List[str]]) -> List[str]:
    """
    Merge multiple tool result lists and deduplicate.

    Args:
        results: Dict of tool_name → list of lines

    Returns:
        Sorted, deduplicated master list
    """
    combined: Set[str] = set()
    for lines in results.values():
        for line in lines:
            cleaned = line.strip().lower()
            if cleaned:
                combined.add(cleaned)
    return sorted(combined)


def merge_urls(results: Dict[str, List[str]]) -> List[str]:
    """
    Merge URL results with noise filtering.

    Args:
        results: Dict of tool_name → list of URLs

    Returns:
        Sorted, deduplicated, cleaned URL list
    """
    combined: Set[str] = set()
    for lines in results.values():
        for line in lines:
            url = line.strip()
            if url and _is_valid_url(url) and not _is_noise_url(url):
                combined.add(url)
    return sorted(combined)


def save_to_file(lines: List[str], path: Path) -> int:
    """
    Save a list of lines to a file.

    Args:
        lines: List of strings to save
        path: Output file path

    Returns:
        Number of lines written
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write("\n".join(lines))
            if lines:
                f.write("\n")
        return len(lines)
    except OSError as e:
        print(f"[!] Could not write {path}: {e}")
        return 0


def load_from_file(path: Path) -> List[str]:
    """
    Load lines from a file.

    Args:
        path: File path to read

    Returns:
        List of non-empty stripped lines
    """
    if not path.exists():
        return []
    try:
        with open(path, "r") as f:
            lines = f.read().splitlines()
        return [line.strip() for line in lines if line.strip()]
    except OSError:
        return []


def filter_subdomains_for_target(subdomains: List[str], target: str) -> List[str]:
    """
    Filter subdomains to only include those belonging to target.

    Args:
        subdomains: List of potential subdomains
        target: Base domain (e.g. target.com)

    Returns:
        Filtered list of valid subdomains
    """
    valid = []
    target_lower = target.lower()
    for sub in subdomains:
        sub_clean = sub.strip().lower()
        if sub_clean.endswith(f".{target_lower}") or sub_clean == target_lower:
            valid.append(sub_clean)
    return sorted(set(valid))


def _is_valid_url(url: str) -> bool:
    """Check if a string looks like a valid URL."""
    return url.startswith(("http://", "https://", "/"))


def _is_noise_url(url: str) -> bool:
    """Check if URL is noise (static assets or katana loop artifacts)."""
    noise_extensions = (
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
        ".css", ".woff", ".woff2", ".ttf", ".eot",
        ".mp4", ".mp3", ".wav", ".avi", ".mov",
        ".pdf", ".doc", ".docx",
    )

    url_lower = url.lower().split("?")[0]

    # Extension check — same as before
    if any(url_lower.endswith(ext) for ext in noise_extensions):
        return True

    # Katana loop artifact check
    try:
        path = url_lower.split("://", 1)[1].split("/", 1)[1] if "/" in url_lower.split("://", 1)[-1] else ""
    except IndexError:
        path = ""

    if path:
        segments = [s for s in path.split("/") if s]

        # Same segment repeating 3+ times = garbage loop
        from collections import Counter
        counts = Counter(segments)
        if any(count >= 3 for count in counts.values()):
            return True

        # Known katana artifact prefixes
        garbage_starts = ("nks/", "atic/", "tic/")
        if any(path.startswith(p) for p in garbage_starts):
            return True

    return False


def chunk_list(items: List[str], chunk_size: int = 1000) -> List[List[str]]:
    """
    Split a large list into chunks for batch processing.

    Args:
        items: List to chunk
        chunk_size: Max items per chunk

    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
