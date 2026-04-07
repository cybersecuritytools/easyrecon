"""
easyrecon Phase 3+4 — Live Detection
Probes subdomains and filters live URLs using httpx.
"""

import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import List, Tuple, Dict

from utils.config import Config
from utils.merger import save_to_file, load_from_file
from utils.display import (
    print_phase_header, print_tool_result, print_warning,
    print_counter, print_phase_skip, print_live_subdomain,
    print_live_tools_spinner,
)
from utils.registry import TOOL_REGISTRY


def run_live_phase(
    subdomains: List[str],
    urls: List[str],
    config: Config,
    output_dir: Path,
) -> Tuple[List[str], List[str], bool]:
    """
    Run Phase 3+4: Live subdomain + URL detection.

    Returns:
        (live_subdomains, live_urls, success)
    """
    if not config.is_tool_enabled("httpx"):
        print_phase_skip("live", "httpx disabled in config")
        return [], [], False

    if not shutil.which("httpx"):
        print_phase_skip("live", "httpx not found — skipping live detection")
        print_warning("Install: go install github.com/projectdiscovery/httpx/cmd/httpx@latest")
        return [], [], False

    processed_dir = output_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    live_subs = []
    live_urls = []

    if subdomains:
        print_phase_header("live")
        live_subs = _probe_subdomains(subdomains, config, processed_dir)
        print_counter("Live subdomains", len(live_subs))

    if urls:
        live_urls = _filter_live_urls(urls, config, processed_dir)
        print_counter("Live URLs", len(live_urls))

    return live_subs, live_urls, True


def _probe_subdomains(
    subdomains: List[str],
    config: Config,
    output_dir: Path,
) -> List[str]:
    """Run httpx on subdomains list."""
    import time

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("\n".join(subdomains))
        tmp_path = Path(f.name)

    timeout = config.get_tool_timeout("httpx")
    
    with print_live_tools_spinner(["httpx (subdomains)"], "live hosts"):
        try:
            start = time.time()
            result = subprocess.run(
                [
                    "httpx",
                    "-l", str(tmp_path),
                    "-silent",
                    "-status-code",
                    "-title",
                    "-server",
                    "-tech-detect",
                    "-timeout", "10",
                    "-threads", str(config.threads),
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            elapsed = time.time() - start
    
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
            save_to_file(lines, output_dir / "live_subdomains.txt")
    
            print_tool_result("httpx", "success", len(lines), elapsed)
    
            for line in lines[:5]:
                parts = _parse_httpx_line(line)
                if parts:
                    print_live_subdomain(*parts)
    
            return lines
    
        except subprocess.TimeoutExpired:
            print_warning("httpx timeout on subdomains — partial results")
            return []
        except Exception as e:
            print_warning(f"httpx error: {e}")
            return []
        finally:
            tmp_path.unlink(missing_ok=True)


def _filter_live_urls(
    urls: List[str],
    config: Config,
    output_dir: Path,
) -> List[str]:
    """Run httpx on URLs to filter live ones."""
    import time

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("\n".join(urls))
        tmp_path = Path(f.name)

    timeout = config.get_tool_timeout("httpx")

    with print_live_tools_spinner(["httpx (urls)"], "live urls"):
        try:
            start = time.time()
            result = subprocess.run(
                [
                    "httpx",
                    "-l", str(tmp_path),
                    "-silent",
                    "-status-code",
                    "-timeout", "10",
                    "-threads", "100",
                    "-mc", "200,301,302,403,401,405",
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            elapsed = time.time() - start
    
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
            save_to_file(lines, output_dir / "live_urls.txt")
    
            print_tool_result("httpx (urls)", "success", len(lines), elapsed)
            return lines
    
        except subprocess.TimeoutExpired:
            print_warning("httpx timeout on URLs — partial results")
            return []
        except Exception as e:
            print_warning(f"httpx URL filter error: {e}")
            return []
        finally:
            tmp_path.unlink(missing_ok=True)


def _parse_httpx_line(line: str) -> Tuple:
    """Parse an httpx output line into components."""
    try:
        parts = line.split()
        host = parts[0] if parts else ""
        status = ""
        title = ""
        server = ""
        tech = ""
        for part in parts[1:]:
            if part.startswith("[") and part.endswith("]"):
                inner = part[1:-1]
                if inner.isdigit():
                    status = inner
                elif not title:
                    title = inner
                elif not server:
                    server = inner
                else:
                    tech = inner
        return host, status, title, server, tech
    except Exception:
        return None
