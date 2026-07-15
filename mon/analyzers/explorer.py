from __future__ import annotations

from mon.analyzers.base import BaseAnalyzer
from mon.analyzers.route_tree import build_tree, render_root, tree_to_dict
from mon.constants import ACTION_ROUTES
from mon.engine.context import InspectContext


class ExplorerAnalyzer(BaseAnalyzer):
    """Builds a file-manager-style tree from the route list: folders always
    before files, alphabetical within each group, at every depth -- never
    the raw crawler discovery order."""

    name = "explorer"
    description = "Build the folder-first, alphabetically sorted route explorer."
    priority = 60
    dependencies: tuple[str, ...] = (ACTION_ROUTES,)

    def run(self, context: InspectContext) -> None:
        tree = build_tree(context.routes)
        context.explorer_tree = {
            "domain": context.config.domain,
            "tree": tree_to_dict(tree),
        }
        context.explorer_visual = "\n".join(render_root(context.config.domain, tree))

    def summary(self, context: InspectContext) -> str | None:
        return f"explorer tree built ({len(context.routes)} routes)"
