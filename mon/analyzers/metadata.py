from __future__ import annotations

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_CRAWLER, ACTION_METADATA
from mon.engine.context import InspectContext
from mon.parsers.html_parser import HTMLDocument


class MetadataAnalyzer(BaseAnalyzer):
    """Per-page metadata: title, meta description, meta generator tag."""

    name = ACTION_METADATA
    description = "Extract per-page title/description/generator metadata."
    priority = 20
    dependencies: tuple[str, ...] = (ACTION_CRAWLER,)

    def run(self, context: InspectContext) -> None:
        domain = context.config.domain
        for page in context.html_pages():
            doc = HTMLDocument(page.text, page.url, domain)
            context.metadata[page.path] = {
                "title": doc.title,
                "description": doc.meta_description(),
                "generator": doc.meta_generator(),
            }

    def summary(self, context: InspectContext) -> str | None:
        return f"pages with metadata {len(context.metadata)}"
