from __future__ import annotations

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_CRAWLER, ACTION_HTML
from mon.engine.context import InspectContext
from mon.models.script import ScriptRef
from mon.parsers.html_parser import HTMLDocument


class HtmlAnalyzer(BaseAnalyzer):
    """Extracts scripts, images and stylesheets from every crawled HTML page.

    Re-parses ``page.text`` (already in memory from CrawlerAnalyzer) rather
    than re-downloading anything -- per the spec, Context exists precisely so
    this never has to hit the network again.
    """

    name = ACTION_HTML
    description = "Extract scripts/images/stylesheets from crawled HTML pages."
    priority = 10
    dependencies: tuple[str, ...] = (ACTION_CRAWLER,)

    def run(self, context: InspectContext) -> None:
        domain = context.config.domain

        for page in context.html_pages():
            doc = HTMLDocument(page.text, page.url, domain)

            for raw_script in doc.scripts():
                context.scripts.append(
                    ScriptRef(
                        page_url=page.url,
                        src=raw_script.src,
                        inline=raw_script.inline,
                        content=raw_script.content,
                    )
                )

            context.images.extend(doc.images())
            context.stylesheets.extend(doc.stylesheets())

        context.images = sorted(set(context.images))
        context.stylesheets = sorted(set(context.stylesheets))

    def summary(self, context: InspectContext) -> str | None:
        return f"scripts {len(context.scripts)}, images {len(context.images)}, stylesheets {len(context.stylesheets)}"
