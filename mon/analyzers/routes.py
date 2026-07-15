from __future__ import annotations

import posixpath

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_CRAWLER, ACTION_ROUTES
from mon.engine.context import InspectContext
from mon.models.route import Route


def _classify(page_path: str, content_type: str) -> str:
    if page_path.endswith(".js") or "javascript" in content_type:
        return "js"
    if page_path.endswith(".css") or "css" in content_type:
        return "css"
    if "text/html" in content_type:
        return "html"
    return "asset"


class RoutesAnalyzer(BaseAnalyzer):
    """Builds the flat frontend route list. ExplorerAnalyzer later turns this
    into a sorted, folder-first visual tree -- this analyzer only owns the
    underlying route data."""

    name = ACTION_ROUTES
    description = "Build the frontend route list from crawled pages."
    priority = 20
    dependencies: tuple[str, ...] = (ACTION_CRAWLER,)

    def run(self, context: InspectContext) -> None:
        for page in context.pages.values():
            route_type = _classify(page.path, page.content_type)
            file_name = posixpath.basename(page.path) or "index.html"
            context.routes.append(
                Route(
                    path=page.path,
                    file=file_name,
                    type=route_type,
                    title=page.title,
                    is_directory=page.path.endswith("/"),
                )
            )

    def summary(self, context: InspectContext) -> str | None:
        return f"routes {len(context.routes)}"
