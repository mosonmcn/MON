from __future__ import annotations

import posixpath

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_ASSETS, ACTION_HTML
from mon.engine.context import InspectContext

_FONT_EXTENSIONS = (".woff", ".woff2", ".ttf", ".eot", ".otf")
_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico")


def _categorize(path: str) -> str:
    ext = posixpath.splitext(path)[1].lower()
    if ext in _FONT_EXTENSIONS:
        return "fonts"
    if ext in _IMAGE_EXTENSIONS:
        return "images"
    if ext == ".css":
        return "css"
    if ext == ".js":
        return "javascript"
    return "other"


class AssetsAnalyzer(BaseAnalyzer):
    """Categorizes every static asset discovered so far into css/images/fonts/js/other."""

    name = ACTION_ASSETS
    description = "Categorize CSS/images/fonts/JS assets discovered during crawl."
    priority = 20
    dependencies: tuple[str, ...] = (ACTION_HTML,)

    def run(self, context: InspectContext) -> None:
        buckets: dict[str, set[str]] = {
            "css": set(), "images": set(), "fonts": set(), "javascript": set(), "other": set(),
        }

        for path in context.stylesheets:
            buckets["css"].add(path)
        for path in context.images:
            buckets[_categorize(path)].add(path)
        for page in context.pages.values():
            if page.is_javascript:
                buckets["javascript"].add(page.path)
            elif page.is_css:
                buckets["css"].add(page.path)

        context.assets = {category: sorted(paths) for category, paths in buckets.items()}

    def summary(self, context: InspectContext) -> str | None:
        total = sum(len(v) for v in context.assets.values())
        return f"assets {total}"
