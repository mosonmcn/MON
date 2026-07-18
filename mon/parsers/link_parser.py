"""Universal Link Scanner -- THIS IS CLONER'S ORIGINAL parser.py LOGIC,
ported as-is (same regex patterns, same HTML tag scan, same domain check).
Only the packaging changed: it's now a function analyzers call through
context, instead of a bare module-level import in main.py.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


def extract_paths(html_or_js_content, current_url: str, domain: str) -> list[str]:
    """Yana ciro hanyoyin sadarwa daga HTML links, kuma yana shiga cikin JS
    code don zakulo window.location ko redirect paths."""
    discovered_paths: set[str] = set()

    if isinstance(html_or_js_content, bytes):
        try:
            content_str = html_or_js_content.decode("utf-8", errors="ignore")
        except Exception:
            return []
    else:
        content_str = html_or_js_content

    # --- SASHEN NA 1: FARAUTAR LINKS A CIKIN HTML ---
    try:
        soup = BeautifulSoup(content_str, "html.parser")
        for tag in soup.find_all(["a", "link", "script", "img", "iframe"], href=True):
            href = tag.get("href")
            if href:
                _process_raw_link(href, current_url, domain, discovered_paths)
        for tag in soup.find_all(["script", "img", "iframe", "source"], src=True):
            src = tag.get("src")
            if src:
                _process_raw_link(src, current_url, domain, discovered_paths)
    except Exception:
        pass

    # --- SASHEN NA 2: UNIVERSAL JS ROUTER LINK SCANNER ---
    js_patterns = [
        r'(?:window\.)?location(?:\.href)?\s*=\s*[\'"`]([^\'"`]+)[\'"`]',
        r'(?:window\.)?location\.replace\(\s*[\'"`]([^\'"`]+)[\'"`]\s*\)',
        r'(?:window\.)?location\.assign\(\s*[\'"`]([^\'"`]+)[\'"`]\s*\)',
        r'href\s*:\s*[\'"`](/[^\'"`]+)[\'"`]',
        r'url\s*:\s*[\'"`](/[^\'"`]+)[\'"`]',
    ]

    for pattern in js_patterns:
        js_links = re.findall(pattern, content_str)
        for link in js_links:
            if link and not link.startswith("http") and ("." in link or "/" in link or len(link) > 3):
                _process_raw_link(link, current_url, domain, discovered_paths)

    return list(discovered_paths)


def _process_raw_link(raw_link: str, current_url: str, domain: str, path_set: set[str]) -> None:
    raw_link = raw_link.strip()

    if raw_link.lower().startswith("javascript:") or raw_link.startswith("#"):
        return

    # Kariya daga JS template-literal placeholders (misali
    # `/js/modules/${escapeHtml(d.payment_url)}` ko `/${id}`). Wadannan ba
    # URL na gaskiya ba ne -- variable ne da za a maye gurbinsu a runtime --
    # don haka ba za mu aika fetch request zuwa gare su ba. Wannan sabon
    # tacewa ne kawai a wannan ported copy (cloner_mon); ba a taba ainihin
    # cloner.zip ko MON-3.zip ba.
    if "${" in raw_link or "{{" in raw_link:
        return

    absolute_url = urljoin(current_url, raw_link)
    parsed_url = urlparse(absolute_url)

    if parsed_url.netloc == domain or parsed_url.netloc == f"www.{domain}":
        clean_path = parsed_url.path
        if not clean_path:
            clean_path = "/"
        path_set.add(clean_path)


def get_html_title(html_content: str) -> str:
    """Cloner's explorer.get_html_title, adapted to operate on already-
    fetched content instead of re-reading from disk."""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        if soup.title and soup.title.string:
            return soup.title.string.strip()
    except Exception:
        pass
    return "Untitled Page"
