from __future__ import annotations

import json
from dataclasses import asdict

from mon.exporters.base import BaseExporter
from mon.models.result import InspectResult


class JsonExporter(BaseExporter):
    extension = ".json"

    def export(self, result: InspectResult) -> str:
        return json.dumps(asdict(result), indent=2, ensure_ascii=False, default=str)
