"""RoutesAnalyzer -- builds the flat Route list combining frontend pages
(from the crawl) and backend endpoints (from ApiAnalyzer), same split
cloner's explorer.generate_website_explorer() did internally.
"""

from __future__ import annotations

import os

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_API, ACTION_CRAWLER, ACTION_ROUTES
from mon.engine.context import InspectContext
from mon.models.route import Route


class RoutesAnalyzer(BaseAnalyzer):
    name = ACTION_ROUTES
    description = "Builds the combined frontend + backend route map."
    priority = 40
    dependencies: tuple[str, ...] = (ACTION_CRAWLER, ACTION_API)

    def run(self, context: InspectContext) -> None:
        for path, page in context.pages.items():
            if page.is_html:
                route_path = path if path.endswith("/") or path == "/" else path + "/"
                context.routes.append(Route(
                    path=route_path, file="index.html", type="html",
                    format=".html", title=page.title,
                ))
            else:
                ext = os.path.splitext(path)[1].lower() or ""
                ftype = ext.lstrip(".") if ext else "unknown"
                context.routes.append(Route(
                    path=path, file=os.path.basename(path) or path,
                    type=ftype, format=ext,
                ))

        for endpoint in context.endpoints:
            context.routes.append(Route(
                path=endpoint.url,
                file=endpoint.url.rsplit("/", 1)[-1] or "index.php",
                type="json",
                format=os.path.splitext(endpoint.url)[1].lower() or ".php",
            ))

    def summary(self, context: InspectContext) -> str | None:
        return f"routes {len(context.routes)}"
