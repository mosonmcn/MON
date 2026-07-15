from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse

from mon.network.fetcher import Fetcher

logger = logging.getLogger("mon.network.robots")

_SITEMAP_TAG_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.IGNORECASE)


def discover_seed_paths(base_url: str, fetcher: Fetcher) -> list[str]:
    """Look at /robots.txt (and any Sitemap: entries it points to) to find
    extra seed paths the crawler would otherwise only discover by luck.

    Failures here are non-fatal -- most sites don't have a useful robots.txt,
    and that must never stop the rest of the inspection.
    """
    seeds: list[str] = []

    robots_url = urljoin(base_url, "/robots.txt")
    try:
        response = fetcher.get(robots_url)
    except Exception:  # noqa: BLE001
        return seeds

    if not response.ok:
        return seeds

    sitemap_urls: list[str] = []
    for line in response.text.splitlines():
        line = line.strip()
        if line.lower().startswith("sitemap:"):
            sitemap_urls.append(line.split(":", 1)[1].strip())
        elif line.lower().startswith(("allow:", "disallow:")):
            path = line.split(":", 1)[1].strip()
            if path and path != "/" and not path.startswith("*"):
                seeds.append(path)

    for sitemap_url in sitemap_urls[:3]:  # cap: don't chase an unbounded sitemap index
        try:
            sitemap_response = fetcher.get(sitemap_url)
        except Exception:  # noqa: BLE001
            continue
        if not sitemap_response.ok:
            continue
        for match in _SITEMAP_TAG_RE.finditer(sitemap_response.text):
            loc = match.group(1)
            parsed = urlparse(loc)
            if parsed.path:
                seeds.append(parsed.path)

    # de-duplicate while preserving order
    seen: set[str] = set()
    unique_seeds: list[str] = []
    for path in seeds:
        if path not in seen:
            seen.add(path)
            unique_seeds.append(path)
    return unique_seeds
