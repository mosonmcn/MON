from __future__ import annotations

from mon.exceptions import ExportError
from mon.exporters.base import BaseExporter
from mon.exporters.json_exporter import JsonExporter
from mon.exporters.markdown_exporter import MarkdownExporter

_EXPORTERS: dict[str, type[BaseExporter]] = {
    "json": JsonExporter,
    "markdown": MarkdownExporter,
}


def get_exporter(output_format: str) -> BaseExporter:
    try:
        return _EXPORTERS[output_format]()
    except KeyError as exc:
        raise ExportError(f"Unknown output_format '{output_format}'.") from exc
