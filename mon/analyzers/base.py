"""Base class every analyzer must inherit (structure taken from MON).

Each analyzer is a class, one per file, exposing name/description/priority/
dependencies/run(). None of them call print() -- progress goes exclusively
through InspectContext's event bus.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from mon.engine.context import InspectContext
from mon.engine.events import ANALYZER_AFTER_RUN, ANALYZER_BEFORE_RUN


class BaseAnalyzer(ABC):
    name: str = "base"
    description: str = ""
    priority: int = 100
    dependencies: tuple[str, ...] = ()

    def before_run(self, context: InspectContext) -> None:
        pass

    @abstractmethod
    def run(self, context: InspectContext) -> None:
        ...

    def after_run(self, context: InspectContext) -> None:
        pass

    def summary(self, context: InspectContext) -> str | None:
        return None

    def execute(self, context: InspectContext) -> None:
        context.events.emit(ANALYZER_BEFORE_RUN, analyzer=self.name)
        self.before_run(context)
        self.run(context)
        self.after_run(context)
        context.completed_actions.add(self.name)
        context.events.emit(ANALYZER_AFTER_RUN, analyzer=self.name, summary=self.summary(context))
