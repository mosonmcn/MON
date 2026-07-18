from __future__ import annotations

from mon.exporters.base import BaseExporter
from mon.models.result import InspectResult


class MarkdownExporter(BaseExporter):
    extension = ".md"

    def export(self, result: InspectResult) -> str:
        lines = [
            f"# Inspection Report -- {result.domain}",
            "",
            f"- Pages crawled: {result.pages_crawled}",
            f"- Routes discovered: {len(result.routes)}",
            f"- API endpoints reconstructed: {len(result.api_spec)}",
            f"- Static assets: {result.assets_saved}",
            f"- Actions run: {', '.join(result.actions_run)}",
            "",
            "## API Spec",
            "",
        ]
        for url, spec in result.api_spec.items():
            lines.append(f"### `{spec.get('method', 'GET')} {url}`")
            lines.append(f"- Purpose: {spec.get('function_purpose')}")
            lines.append(f"- Payload format: {spec.get('expected_payload_format')}")
            lines.append(f"- Confidence: {spec.get('confidence', {}).get('score')}")
            lines.append("")
        if result.warnings:
            lines.append("## Warnings")
            for w in result.warnings:
                lines.append(f"- {w}")
        return "\n".join(lines)
