from __future__ import annotations

from abc import ABC, abstractmethod

from mon.models.result import InspectResult


class BaseExporter(ABC):
    extension: str = ".txt"

    @abstractmethod
    def export(self, result: InspectResult) -> str:
        ...
