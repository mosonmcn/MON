"""HtmlAnalyzer -- pulls titles out of already-crawled HTML pages.

Uses cloner's original get_html_title() logic (mon.parsers.link_parser),
just reading from context.pages instead of from disk.
"""

from __future__ import annotations

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_CRAWLER, ACTION_HTML
from mon.engine.context import InspectContext
from mon.parsers.link_parser import get_html_title


class HtmlAnalyzer(BaseAnalyzer):
    name = ACTION_HTML
    description = "Extracts <title> and structural metadata from crawled HTML pages."
    priority = 10
    dependencies: tuple[str, ...] = (ACTION_CRAWLER,)

    def run(self, context: InspectContext) -> None:
        for page in context.html_pages():
            page.title = get_html_title(page.text)

    def summary(self, context: InspectContext) -> str | None:
        return f"titles {len(context.html_pages())}"
