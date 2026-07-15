"""Event system.

Analyzers and the dispatcher never print anything directly. Instead they
``emit()`` an event on the shared :class:`EventBus`, and anything that wants
to observe progress (the built-in :class:`~mon.engine.progress.ProgressManager`,
a future AI layer, a third-party plugin) calls :meth:`EventBus.subscribe`.
This keeps every analyzer's responsibility limited to analysis -- how (or
whether) progress is surfaced to the user is a completely separate concern.
"""

from __future__ import annotations

from typing import Callable, Final

EventCallback = Callable[..., None]

# --------------------------------------------------------------------------- #
# Canonical event names -- using constants instead of raw strings avoids typos
# silently breaking a subscription.
# --------------------------------------------------------------------------- #

INSPECTION_STARTED: Final[str] = "inspection.started"
INSPECTION_COMPLETED: Final[str] = "inspection.completed"
INSPECTION_FAILED: Final[str] = "inspection.failed"

PAGE_DOWNLOADED: Final[str] = "page.downloaded"
PAGE_SKIPPED: Final[str] = "page.skipped"

ANALYZER_BEFORE_RUN: Final[str] = "analyzer.before_run"
ANALYZER_AFTER_RUN: Final[str] = "analyzer.after_run"
ANALYZER_FAILED: Final[str] = "analyzer.failed"

EXPORT_COMPLETED: Final[str] = "export.completed"


class EventBus:
    """A minimal synchronous publish/subscribe bus."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventCallback]] = {}

    def subscribe(self, event_name: str, callback: EventCallback) -> None:
        self._subscribers.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name: str, callback: EventCallback) -> None:
        if event_name in self._subscribers:
            self._subscribers[event_name] = [
                cb for cb in self._subscribers[event_name] if cb is not callback
            ]

    def emit(self, event_name: str, **payload: object) -> None:
        for callback in self._subscribers.get(event_name, []):
            callback(event=event_name, **payload)
