"""Constants shared across the engine.

Nothing here holds mutable state, so it's safe to import from anywhere
without creating import cycles.

NOTE on networking defaults: unlike MON's own constants module, this file
does NOT define DEFAULT_HEADERS / retry policy. Network behaviour is owned
entirely by ``mon.network.fetcher`` (cloner's original, simpler fetch logic),
kept deliberately separate so the "how we talk to a website" concern never
leaks into the engine layer.
"""

from __future__ import annotations

from typing import Final

# --------------------------------------------------------------------------- #
# Profiles control crawl depth/breadth.
# --------------------------------------------------------------------------- #

PROFILE_FAST: Final[str] = "fast"
PROFILE_BALANCED: Final[str] = "balanced"
PROFILE_DEEP: Final[str] = "deep"
VALID_PROFILES: Final[tuple[str, ...]] = (PROFILE_FAST, PROFILE_BALANCED, PROFILE_DEEP)

PROFILE_SETTINGS: Final[dict[str, dict[str, float | int | bool]]] = {
    PROFILE_FAST: {"max_page": 15, "delay_seconds": 0.0, "live_verify": False},
    PROFILE_BALANCED: {"max_page": 100, "delay_seconds": 0.0, "live_verify": True},
    PROFILE_DEEP: {"max_page": 500, "delay_seconds": 0.0, "live_verify": True},
}

# --------------------------------------------------------------------------- #
# Output formats supported by exporters/registry.py
# --------------------------------------------------------------------------- #

FORMAT_JSON: Final[str] = "json"
FORMAT_MARKDOWN: Final[str] = "markdown"
VALID_OUTPUT_FORMATS: Final[tuple[str, ...]] = (FORMAT_JSON, FORMAT_MARKDOWN)

# --------------------------------------------------------------------------- #
# Leaf actions -- map 1:1 to a single analyzer in the registry. This list
# only covers what the original cloner project actually did: crawl pages,
# read links out of HTML, read API calls out of JS, live-verify those APIs,
# build a route list, save static assets, and build the explorer tree.
# MON's own extra analyzers (forms, technology, server_info, metadata,
# relationships) had no equivalent in cloner, so they are intentionally not
# reproduced here rather than being faked with empty stubs.
# --------------------------------------------------------------------------- #

ACTION_CRAWLER: Final[str] = "crawler"
ACTION_HTML: Final[str] = "html"
ACTION_JAVASCRIPT: Final[str] = "javascript"
ACTION_API: Final[str] = "api"
ACTION_ROUTES: Final[str] = "routes"
ACTION_ASSETS: Final[str] = "assets"
ACTION_EXPLORER: Final[str] = "explorer"

LEAF_ACTIONS: Final[tuple[str, ...]] = (
    ACTION_CRAWLER, ACTION_HTML, ACTION_JAVASCRIPT, ACTION_API,
    ACTION_ROUTES, ACTION_ASSETS, ACTION_EXPLORER,
)

# --------------------------------------------------------------------------- #
# Composite actions -- expand into a group of leaf actions (single source of
# truth for expansion, used by engine/resolver.py).
# --------------------------------------------------------------------------- #

ACTION_ALL_DATA: Final[str] = "all_data"
ACTION_API_SPEC: Final[str] = "api_spec"
ACTION_EXPLORER_VISUAL: Final[str] = "explorer_visual"
ACTION_CLONING: Final[str] = "cloning"

ACTION_GROUPS: Final[dict[str, tuple[str, ...]]] = {
    ACTION_API_SPEC: (ACTION_CRAWLER, ACTION_HTML, ACTION_JAVASCRIPT, ACTION_API),
    ACTION_EXPLORER_VISUAL: (ACTION_CRAWLER, ACTION_HTML, ACTION_ROUTES, ACTION_EXPLORER),
    ACTION_CLONING: (ACTION_CRAWLER, ACTION_HTML, ACTION_ASSETS),
    ACTION_ALL_DATA: LEAF_ACTIONS,
}

STATIC_ASSET_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
     ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".pdf"}
)
