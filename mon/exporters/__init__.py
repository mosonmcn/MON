from mon.constants import FORMAT_HTML, FORMAT_JSON, FORMAT_MARKDOWN, FORMAT_PYTHON, FORMAT_YAML
from mon.exceptions import ExportError
from mon.exporters.base import BaseExporter
from mon.exporters.html_exporter import HtmlExporter
from mon.exporters.json_exporter import JsonExporter
from mon.exporters.markdown_exporter import MarkdownExporter
from mon.exporters.python_exporter import PythonExporter
from mon.exporters.yaml_exporter import YamlExporter

_EXPORTERS: dict[str, type[BaseExporter]] = {
    FORMAT_JSON: JsonExporter,
    FORMAT_YAML: YamlExporter,
    FORMAT_PYTHON: PythonExporter,
    FORMAT_MARKDOWN: MarkdownExporter,
    FORMAT_HTML: HtmlExporter,
}


def get_exporter(output_format: str) -> BaseExporter:
    try:
        return _EXPORTERS[output_format]()
    except KeyError as exc:
        raise ExportError(
            f"No exporter registered for format '{output_format}'. "
            f"Available formats: {sorted(_EXPORTERS)}"
        ) from exc


__all__ = [
    "BaseExporter",
    "HtmlExporter",
    "JsonExporter",
    "MarkdownExporter",
    "PythonExporter",
    "YamlExporter",
    "get_exporter",
]
