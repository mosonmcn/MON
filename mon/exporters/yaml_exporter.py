from __future__ import annotations

import yaml

from mon.exporters.base import BaseExporter
from mon.models.result import InspectResult


class YamlExporter(BaseExporter):
    extension = ".yaml"

    def export(self, result: InspectResult) -> str:
        return yaml.safe_dump(result.to_dict(), sort_keys=False, allow_unicode=True)
