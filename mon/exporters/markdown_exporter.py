from __future__ import annotations

import json

from mon.exporters.base import BaseExporter
from mon.models.result import InspectResult


class MarkdownExporter(BaseExporter):
    extension = ".md"

    def export(self, result: InspectResult) -> str:
        lines: list[str] = []
        lines.append(f"# MON Inspection Report -- {result.domain}")
        lines.append("")
        lines.append(f"- Pages crawled: **{result.pages_crawled}**")
        lines.append(f"- Actions run: `{', '.join(result.actions_run)}`")
        lines.append(f"- Endpoints found: **{len(result.apis)}**")
        lines.append(f"- Forms found: **{len(result.forms)}**")
        if result.technology:
            tech_names = ", ".join(t.name for t in result.technology)
            lines.append(f"- Technology detected: {tech_names}")
        lines.append("")

        if result.apis:
            lines.append("## API Specification")
            lines.append("")
            for endpoint in result.apis:
                lines.append(f"### `{endpoint.method} {endpoint.url}`")
                lines.append("")
                lines.append(f"- **Confidence:** {endpoint.confidence.score}%")
                for reason in endpoint.confidence.reasons:
                    lines.append(f"  - {reason}")
                if endpoint.related_html:
                    lines.append(f"- **Related HTML:** `{endpoint.related_html}`")
                if endpoint.related_javascript:
                    lines.append(f"- **Related JavaScript:** `{endpoint.related_javascript}`")
                if endpoint.related_form:
                    lines.append(f"- **Related Form:** `{endpoint.related_form}`")
                if endpoint.request_schema:
                    lines.append("")
                    lines.append("**Payload / Parameters**")
                    lines.append("```json")
                    lines.append(json.dumps(endpoint.request_schema, indent=2))
                    lines.append("```")
                if endpoint.response_schema:
                    lines.append("")
                    lines.append("**Response Schema (success)**")
                    lines.append("```json")
                    lines.append(json.dumps(endpoint.response_schema, indent=2))
                    lines.append("```")
                if endpoint.error_schema:
                    lines.append("")
                    lines.append("**Response Schema (error)**")
                    lines.append("```json")
                    lines.append(json.dumps(endpoint.error_schema, indent=2))
                    lines.append("```")
                if endpoint.live_verified:
                    lines.append("")
                    lines.append(f"**Live-verified sample response:**")
                    lines.append("```json")
                    lines.append(json.dumps(endpoint.live_sample_response, indent=2, default=str))
                    lines.append("```")
                lines.append("")

        if result.forms:
            lines.append("## Forms")
            lines.append("")
            for form in result.forms:
                lines.append(f"- `{form.method} {form.action}` -- fields: {', '.join(form.field_names) or '(none)'}")
            lines.append("")

        if result.explorer_visual:
            lines.append("## Explorer")
            lines.append("")
            lines.append("```")
            lines.append(result.explorer_visual)
            lines.append("```")
            lines.append("")

        if result.relationships:
            lines.append("## Relationships")
            lines.append("")
            for rel in result.relationships:
                lines.append(f"- {rel.describe()} (confidence: {rel.confidence}%)")
            lines.append("")

        if result.warnings:
            lines.append("## Warnings")
            lines.append("")
            for warning in result.warnings:
                lines.append(f"- {warning}")
            lines.append("")

        return "\n".join(lines)
