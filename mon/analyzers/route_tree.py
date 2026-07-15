"""Folder-first, alphabetically sorted route tree.

Extracted from ExplorerAnalyzer so it can be reused by
mon.engine.output_writer to rebuild a consistent tree from merged route
data (current run plus whatever a previous run already wrote to disk),
not just whatever routes happened to be discovered in the current run.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mon.models.route import Route

FOLDER_ICON = "📁"
FILE_ICON = "📄"


@dataclass(slots=True)
class RouteTreeNode:
    name: str
    children: dict[str, "RouteTreeNode"] = field(default_factory=dict)
    route: Route | None = None

    @property
    def is_folder(self) -> bool:
        return bool(self.children)

    @property
    def represents_page(self) -> bool:
        """True if this node itself corresponds to a crawled HTML page
        (as opposed to being purely an intermediate path segment with no
        content of its own, e.g. '/dashboard' in a site that only has
        '/dashboard/settings' but no '/dashboard' page itself)."""
        return self.route is not None and self.route.type == "html"


def build_tree(routes: list[Route]) -> RouteTreeNode:
    root = RouteTreeNode(name="")
    for route in routes:
        parts = [p for p in route.path.split("/") if p]
        if not parts:
            root.route = route
            continue
        cursor = root
        for index, part in enumerate(parts):
            cursor = cursor.children.setdefault(part, RouteTreeNode(name=part))
            if index == len(parts) - 1:
                cursor.route = route
    return root


def _visual_is_folder(node: RouteTreeNode) -> bool:
    """A node renders as a folder if it has real children, OR if it is
    itself an HTML page -- since every HTML route is written to disk as
    <route>/index.html (a directory), never a flat <route> file."""
    return node.is_folder or node.represents_page


def render_visual(node: RouteTreeNode, indent: str = "") -> list[str]:
    folders = sorted((c for c in node.children.values() if _visual_is_folder(c)), key=lambda n: n.name.lower())
    files = sorted((c for c in node.children.values() if not _visual_is_folder(c)), key=lambda n: n.name.lower())
    ordered = folders + files

    lines: list[str] = []
    for i, child in enumerate(ordered):
        is_last = i == len(ordered) - 1
        connector = "└── " if is_last else "├── "
        is_child_folder = _visual_is_folder(child)
        icon = FOLDER_ICON if is_child_folder else FILE_ICON
        title_tag = f"  ({child.route.title})" if (child.route and child.route.title) else ""
        lines.append(f"{indent}{connector}{icon} {child.name}{'/' if is_child_folder else ''}{title_tag}")

        if is_child_folder:
            next_indent = indent + ("    " if is_last else "│   ")
            child_lines = render_visual(child, next_indent)
            if child.represents_page:
                index_is_last = not child_lines
                index_connector = "└── " if index_is_last else "├── "
                lines.append(f"{next_indent}{index_connector}{FILE_ICON} index.html")
            lines.extend(child_lines)
    return lines


def render_root(domain: str, root: RouteTreeNode) -> list[str]:
    """Render the full tree including the domain header line and, if the
    root itself corresponds to a crawled page, its own index.html."""
    lines = [f"{FOLDER_ICON} {domain}/"]
    body = render_visual(root)
    if root.route is not None and root.route.type == "html":
        connector = "└── " if not body else "├── "
        lines.append(f"{connector}{FILE_ICON} index.html")
    lines.extend(body)
    return lines


def tree_to_dict(node: RouteTreeNode) -> dict:
    return {
        "name": node.name,
        "type": "folder" if node.is_folder else (node.route.type if node.route else "file"),
        "title": node.route.title if node.route else None,
        "children": [tree_to_dict(c) for c in sorted(
            node.children.values(), key=lambda n: (not n.is_folder, n.name.lower())
        )],
    }
