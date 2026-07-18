"""Inspection context.

All analyzers communicate only through InspectContext -- they never call
each other directly. One analyzer writes to it (e.g. context.pages[path] =
page), a later analyzer reads from it (e.g. context.pages.values()).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mon.config import InspectConfig
from mon.engine.events import EventBus
from mon.models.endpoint import Endpoint
from mon.models.page import Page
from mon.models.route import Route
from mon.network.fetcher import Fetcher


@dataclass(slots=True)
class InspectContext:
    config: InspectConfig
    fetcher: Fetcher
    events: EventBus

    # --- populated by CrawlerAnalyzer ------------------------------------
    pages: dict[str, Page] = field(default_factory=dict)
    visited: set[str] = field(default_factory=set)
    queue: list[str] = field(default_factory=list)

    # --- populated by HtmlAnalyzer ---------------------------------------
    discovered_links: dict[str, set[str]] = field(default_factory=dict)
    """path -> set of paths discovered by that page (HTML links + JS router
    strings), same universal scanner cloner's parser.py used."""

    # --- populated by JavascriptAnalyzer ---------------------------------
    raw_api_spec: dict[str, dict] = field(default_factory=dict)
    """Flat {route: {...}} shape, exactly cloner's advanced_static_analysis
    output, merged across every JS page crawled."""

    # --- populated by ApiAnalyzer -----------------------------------------
    endpoints: list[Endpoint] = field(default_factory=list)

    # --- populated by RoutesAnalyzer / ExplorerAnalyzer --------------------
    routes: list[Route] = field(default_factory=list)
    explorer_tree: dict = field(default_factory=dict)
    explorer_visual: str = ""

    # --- populated by AssetsAnalyzer ---------------------------------------
    assets_saved: int = 0

    # --- bookkeeping ---------------------------------------------------------
    warnings: list[str] = field(default_factory=list)
    completed_actions: set[str] = field(default_factory=set)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def html_pages(self) -> list[Page]:
        return [p for p in self.pages.values() if p.is_html]

    def javascript_pages(self) -> list[Page]:
        return [p for p in self.pages.values() if p.is_javascript]

    def static_asset_pages(self) -> list[Page]:
        return [p for p in self.pages.values() if p.is_static_asset]
