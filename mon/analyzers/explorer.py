"""ExplorerAnalyzer -- builds explorer.json + explorer_visual.txt, the same
two artifacts cloner's original explorer.py produced (route list with
titles, plus an ASCII tree with a simulated backend API section).
"""

from __future__ import annotations

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_API, ACTION_CRAWLER, ACTION_EXPLORER, ACTION_ROUTES
from mon.engine.context import InspectContext


class ExplorerAnalyzer(BaseAnalyzer):
    name = ACTION_EXPLORER
    description = "Builds explorer.json and the ASCII explorer_visual.txt tree."
    priority = 50
    dependencies: tuple[str, ...] = (ACTION_CRAWLER, ACTION_ROUTES, ACTION_API)

    def run(self, context: InspectContext) -> None:
        domain = context.config.domain
        website_routes = []
        for route in context.routes:
            entry = {"path": route.path, "file": route.file, "type": route.type, "format": route.format}
            if route.title is not None:
                entry["title"] = route.title
            website_routes.append(entry)

        context.explorer_tree = {"domain": domain, "website_routes": website_routes}

        # ASCII visual tree, folder-style, cloner's generate_visual_tree shape
        lines = [f"📂 {domain} (Enterprise Frontend Map Layout)"]
        frontend_routes = [r for r in context.routes if r.type != "json"]
        for i, route in enumerate(sorted(frontend_routes, key=lambda r: r.path)):
            is_last = i == len(frontend_routes) - 1
            connector = "└── " if is_last else "├── "
            title_suffix = f"  📌 ({route.title})" if route.title else ""
            lines.append(f"{connector}{route.path}{title_suffix}")

        lines.append("")
        lines.append("⚙️ Simulated Backend API Endpoint Tree")
        api_routes = sorted({r.path for r in context.routes if r.type == "json"})
        if api_routes:
            for i, route in enumerate(api_routes):
                is_last = i == len(api_routes) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{connector}{route}")
        else:
            lines.append("└── [No API Endpoints Captured]")

        context.explorer_visual = "\n".join(lines)

    def summary(self, context: InspectContext) -> str | None:
        return "explorer map built"
