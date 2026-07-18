"""JavascriptAnalyzer -- runs cloner's original advanced_static_analysis
(mon.parsers.js_api_parser) over every crawled JS page and merges the
results into context.raw_api_spec, exactly like cloner's
save_api_spec()/advanced_static_analysis() did in main.py.
"""

from __future__ import annotations

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_CRAWLER, ACTION_JAVASCRIPT
from mon.engine.context import InspectContext
from mon.parsers.js_api_parser import advanced_static_analysis


class JavascriptAnalyzer(BaseAnalyzer):
    name = ACTION_JAVASCRIPT
    description = "Static analysis of JS files to reconstruct backend API calls."
    priority = 20
    dependencies: tuple[str, ...] = (ACTION_CRAWLER,)

    def run(self, context: InspectContext) -> None:
        for page in context.javascript_pages():
            spec = advanced_static_analysis(page.text, current_file_route=page.path)
            context.raw_api_spec.update(spec)

    def summary(self, context: InspectContext) -> str | None:
        return f"candidate endpoints {len(context.raw_api_spec)}"
