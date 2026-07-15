from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from mon.models.result import InspectResult


class BaseExporter(ABC):
    """Every exporter takes an already-built InspectResult and produces one
    representation of it, either as a string (:meth:`export`) or written
    directly to disk (:meth:`write`)."""

    extension: str = ".txt"

    @abstractmethod
    def export(self, result: InspectResult) -> str:
        """Return the result as a string in this exporter's format."""

    def write(self, result: InspectResult, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.export(result), encoding="utf-8")
        return path
