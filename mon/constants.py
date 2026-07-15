"""Constants shared across the MON engine.

Nothing in this module holds mutable state -- it is safe to import from
anywhere without creating import cycles.
"""

from __future__ import annotations

from typing import Final

# --------------------------------------------------------------------------- #
# Networking defaults
# --------------------------------------------------------------------------- #

DEFAULT_TIMEOUT: Final[int] = 15
DEFAULT_USER_AGENT: Final[str] = (
    "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Mobile Safari/537.36 MON-WebIntelligenceEngine/1.0"
)
DEFAULT_HEADERS: Final[dict[str, str]] = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}
RETRY_STATUS_CODES: Final[tuple[int, ...]] = (429, 500, 502, 503, 504)
MAX_RETRIES: Final[int] = 3
BACKOFF_FACTOR: Final[float] = 0.6

# --------------------------------------------------------------------------- #
# Profiles control crawl depth/breadth and how aggressive live-verification is
# --------------------------------------------------------------------------- #

PROFILE_FAST: Final[str] = "fast"
PROFILE_BALANCED: Final[str] = "balanced"
PROFILE_DEEP: Final[str] = "deep"
VALID_PROFILES: Final[tuple[str, ...]] = (PROFILE_FAST, PROFILE_BALANCED, PROFILE_DEEP)

PROFILE_SETTINGS: Final[dict[str, dict[str, float | int | bool]]] = {
    PROFILE_FAST: {"max_page": 15, "delay_seconds": 0.0, "live_verify": False},
    PROFILE_BALANCED: {"max_page": 100, "delay_seconds": 0.35, "live_verify": True},
    PROFILE_DEEP: {"max_page": 500, "delay_seconds": 0.6, "live_verify": True},
}

# --------------------------------------------------------------------------- #
# Output formats supported by exporters/registry.py
# --------------------------------------------------------------------------- #

FORMAT_PYTHON: Final[str] = "python"
FORMAT_JSON: Final[str] = "json"
FORMAT_MARKDOWN: Final[str] = "markdown"
FORMAT_HTML: Final[str] = "html"
FORMAT_YAML: Final[str] = "yaml"
VALID_OUTPUT_FORMATS: Final[tuple[str, ...]] = (
    FORMAT_PYTHON, FORMAT_JSON, FORMAT_MARKDOWN, FORMAT_HTML, FORMAT_YAML,
)

# --------------------------------------------------------------------------- #
# Leaf actions -- these map 1:1 to a single analyzer in the registry.
# --------------------------------------------------------------------------- #

ACTION_CRAWLER: Final[str] = "crawler"
ACTION_HTML: Final[str] = "html"
ACTION_JAVASCRIPT: Final[str] = "javascript"
ACTION_FORMS: Final[str] = "forms"
ACTION_API: Final[str] = "api"
ACTION_ROUTES: Final[str] = "routes"
ACTION_ASSETS: Final[str] = "assets"
ACTION_METADATA: Final[str] = "metadata"
ACTION_TECHNOLOGY: Final[str] = "technology"
ACTION_SERVER: Final[str] = "server_info"
ACTION_RELATIONSHIPS: Final[str] = "relationships"
ACTION_EXPLORER: Final[str] = "explorer"

LEAF_ACTIONS: Final[tuple[str, ...]] = (
    ACTION_CRAWLER, ACTION_HTML, ACTION_JAVASCRIPT, ACTION_FORMS, ACTION_API,
    ACTION_ROUTES, ACTION_ASSETS, ACTION_METADATA, ACTION_TECHNOLOGY,
    ACTION_SERVER, ACTION_RELATIONSHIPS, ACTION_EXPLORER,
)

# --------------------------------------------------------------------------- #
# Composite actions -- these expand into a group of leaf actions. Expansion
# happens in engine/resolver.py; this table is the single source of truth.
# --------------------------------------------------------------------------- #

ACTION_ALL_DATA: Final[str] = "all_data"
ACTION_FRONTEND: Final[str] = "frontend"
ACTION_BACKEND: Final[str] = "backend"
ACTION_API_SPEC: Final[str] = "api_spec"
ACTION_EXPLORER_VISUAL: Final[str] = "explorer_visual"
ACTION_CLONING: Final[str] = "cloning"

ACTION_GROUPS: Final[dict[str, tuple[str, ...]]] = {
    ACTION_FRONTEND: (
        ACTION_CRAWLER, ACTION_HTML, ACTION_ROUTES, ACTION_ASSETS,
        ACTION_METADATA, ACTION_EXPLORER,
    ),
    ACTION_BACKEND: (
        ACTION_CRAWLER, ACTION_HTML, ACTION_JAVASCRIPT, ACTION_FORMS,
        ACTION_API, ACTION_RELATIONSHIPS,
    ),
    ACTION_API_SPEC: (
        ACTION_CRAWLER, ACTION_HTML, ACTION_JAVASCRIPT, ACTION_FORMS,
        ACTION_API, ACTION_RELATIONSHIPS,
    ),
    ACTION_EXPLORER_VISUAL: (ACTION_CRAWLER, ACTION_HTML, ACTION_ROUTES, ACTION_EXPLORER),
    ACTION_CLONING: (ACTION_CRAWLER, ACTION_HTML, ACTION_ASSETS),
    ACTION_ALL_DATA: LEAF_ACTIONS,
}

# --------------------------------------------------------------------------- #
# Misc
# --------------------------------------------------------------------------- #

STATIC_ASSET_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
     ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".pdf"}
)
