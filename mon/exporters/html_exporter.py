from __future__ import annotations

import html as html_escape

from mon.exporters.base import BaseExporter
from mon.exporters.markdown_exporter import MarkdownExporter
from mon.models.result import InspectResult

_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>MON Inspection Report -- {domain}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; color: #1a1a1a; }}
  pre {{ background: #f4f4f5; padding: 1rem; overflow-x: auto; border-radius: 6px; }}
  code {{ background: #f4f4f5; padding: 0.1rem 0.3rem; border-radius: 4px; }}
  h1, h2, h3 {{ border-bottom: 1px solid #e5e5e5; padding-bottom: 0.3rem; }}
</style>
</head>
<body>
<pre>{escaped_markdown}</pre>
</body>
</html>
"""


class HtmlExporter(BaseExporter):
    """A minimal HTML wrapper around the Markdown report. Kept intentionally
    simple (no JS, no external assets) -- it is a document export, not a
    dashboard."""

    extension = ".html"

    def export(self, result: InspectResult) -> str:
        markdown_text = MarkdownExporter().export(result)
        return _TEMPLATE.format(
            domain=html_escape.escape(result.domain),
            escaped_markdown=html_escape.escape(markdown_text),
        )
