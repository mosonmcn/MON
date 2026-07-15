"""Inspection context.

Per the project spec: *"All analyzers communicate only through InspectContext.
Analyzers must never directly communicate with each other."* This class is
the single shared, mutable object that makes that possible -- one analyzer
writes to it (e.g. ``context.pages[url] = page``), a later analyzer reads
from it (e.g. ``context.pages.values()``), and neither ever imports or calls
the other directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mon.config import InspectConfig
from mon.engine.events import EventBus
from mon.models.endpoint import Endpoint
from mon.models.form import Form
from mon.models.page import Page
from mon.models.relationship import RelationshipChain
from mon.models.route import Route
from mon.models.script import ApiCallSite, ScriptRef
from mon.models.technology import ServerInfo, Technology
from mon.network.fetcher import Fetcher
from mon.network.session import SessionManager


@dataclass(slots=True)
class InspectContext:
    """Shared mutable state for a single :func:`mon.inspect` call."""

    config: InspectConfig
    session: SessionManager
    fetcher: Fetcher
    events: EventBus

    # --- populated by CrawlerAnalyzer -----------------------------------
    pages: dict[str, Page] = field(default_factory=dict)
    """Keyed by path (e.g. '/', '/login')."""
    visited: set[str] = field(default_factory=set)
    queue: list[str] = field(default_factory=list)

    # --- populated by HtmlAnalyzer ---------------------------------------
    scripts: list[ScriptRef] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    stylesheets: list[str] = field(default_factory=list)

    # --- populated by AssetsAnalyzer ---------------------------------------
    assets: dict[str, list[str]] = field(default_factory=dict)

    # --- populated by JavascriptAnalyzer ---------------------------------
    api_call_sites: list[ApiCallSite] = field(default_factory=list)

    # --- populated by FormsAnalyzer ---------------------------------------
    forms: list[Form] = field(default_factory=list)

    # --- populated by ApiAnalyzer -------------------------------------
    endpoints: list[Endpoint] = field(default_factory=list)

    # --- populated by RoutesAnalyzer / ExplorerAnalyzer -------------------
    routes: list[Route] = field(default_factory=list)
    explorer_tree: dict = field(default_factory=dict)
    explorer_visual: str = ""

    # --- populated by MetadataAnalyzer --------------------------------------
    metadata: dict[str, dict] = field(default_factory=dict)
    """Keyed by page path."""

    # --- populated by TechnologyAnalyzer / ServerAnalyzer ------------------
    technologies: list[Technology] = field(default_factory=list)
    server_info: ServerInfo | None = None

    # --- populated by RelationshipsAnalyzer --------------------------------
    relationships: list[RelationshipChain] = field(default_factory=list)

    # --- bookkeeping --------------------------------------------------------
    warnings: list[str] = field(default_factory=list)
    completed_actions: set[str] = field(default_factory=set)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def html_pages(self) -> list[Page]:
        return [p for p in self.pages.values() if p.is_html]

    def javascript_pages(self) -> list[Page]:
        return [p for p in self.pages.values() if p.is_javascript]
