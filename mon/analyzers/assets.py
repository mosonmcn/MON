"""AssetsAnalyzer -- counts/marks non-HTML/JS static assets (images, CSS,
fonts, ...) that were pulled down by the crawl. Actual writing to disk
happens in output_writer.py (which uses cloner's original
path_to_local rules) once, at the end of the run -- this analyzer just
tallies what's there for the summary/report.
"""

from __future__ import annotations

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_ASSETS, ACTION_CRAWLER
from mon.engine.context import InspectContext


class AssetsAnalyzer(BaseAnalyzer):
    name = ACTION_ASSETS
    description = "Tallies static assets (CSS/images/fonts/etc) discovered during the crawl."
    priority = 15
    dependencies: tuple[str, ...] = (ACTION_CRAWLER,)

    def run(self, context: InspectContext) -> None:
        context.assets_saved = len(context.static_asset_pages())

    def summary(self, context: InspectContext) -> str | None:
        return f"static assets {context.assets_saved}"
