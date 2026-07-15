from __future__ import annotations

import posixpath
from urllib.parse import urljoin, urlparse


def same_domain(url: str, domain: str) -> bool:
    parsed_domain = urlparse(url).netloc.split(":")[0].removeprefix("www.")
    target_domain = domain.split(":")[0].removeprefix("www.")
    return parsed_domain == target_domain


def normalize_path(raw_link: str, current_url: str, domain: str) -> str | None:
    """Resolve a raw href/src value against the current page URL and return a
    clean, same-domain path (starting with '/'), or ``None`` if the link is
    off-domain, a fragment, a mailto/tel/javascript pseudo-link, or empty.
    """
    if not raw_link:
        return None

    stripped = raw_link.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return None

    absolute = urljoin(current_url, stripped)
    if not same_domain(absolute, domain):
        return None

    parsed = urlparse(absolute)
    path = parsed.path or "/"
    return path


def resolve_api_path(current_file_route: str, base_api_url: str, endpoint_path: str) -> str:
    """Resolve an endpoint path referenced inside a JS file into an absolute
    route, taking the JS file's own location and any detected API_BASE_URL
    constant into account."""
    if endpoint_path.startswith(("http://", "https://")):
        return urlparse(endpoint_path).path

    current_dir = posixpath.dirname(current_file_route)

    if base_api_url and not base_api_url.startswith("http"):
        combined_base = posixpath.normpath(posixpath.join(current_dir, base_api_url))
    else:
        combined_base = current_dir if not base_api_url else "/api"

    final_path = posixpath.normpath(posixpath.join(combined_base, endpoint_path))
    final_path = final_path.split("?")[0]
    if not final_path.startswith("/"):
        final_path = "/" + final_path
    return final_path
