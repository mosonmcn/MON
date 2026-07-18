"""Event system (structure taken from MON).

Analyzers never call print() directly -- they emit() an event on the shared
EventBus, and anything that wants to observe progress (ProgressManager, a
future AI layer, a third-party plugin) subscribes. This keeps each
analyzer's job limited to analysis.
"""

from __future__ import annotations

from typing import Callable, Final

EventCallback = Callable[..., None]

INSPECTION_STARTED: Final[str] = "inspection.started"
INSPECTION_COMPLETED: Final[str] = "inspection.completed"
INSPECTION_FAILED: Final[str] = "inspection.failed"

PAGE_DOWNLOADED: Final[str] = "page.downloaded"
PAGE_SKIPPED: Final[str] = "page.skipped"

ANALYZER_BEFORE_RUN: Final[str] = "analyzer.before_run"
ANALYZER_AFTER_RUN: Final[str] = "analyzer.after_run"
ANALYZER_FAILED: Final[str] = "analyzer.failed"


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventCallback]] = {}

    def subscribe(self, event_name: str, callback: EventCallback) -> None:
        self._subscribers.setdefault(event_name, []).append(callback)

    def emit(self, event_name: str, **payload: object) -> None:
        for callback in self._subscribers.get(event_name, []):
            callback(event=event_name, **payload)
