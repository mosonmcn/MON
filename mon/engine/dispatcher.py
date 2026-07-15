"""Dispatcher.

Executes an already-resolved pipeline of analyzer classes, in order,
against one shared :class:`~mon.engine.context.InspectContext`. This module
contains no ``if/elif`` branching on action names -- that logic lives in the
Resolver/Registry. The Dispatcher's only job is: instantiate, execute, handle
failure, move on.
"""

from __future__ import annotations

import logging

from mon.analyzers.base import BaseAnalyzer
from mon.engine.context import InspectContext
from mon.engine.events import ANALYZER_FAILED
from mon.exceptions import AnalyzerError

logger = logging.getLogger("mon.engine.dispatcher")


class Dispatcher:
    """Runs an ordered analyzer pipeline against a shared context.

    ``fail_fast=False`` (the default) means one analyzer failing does not
    abort the whole inspection -- the failure is recorded as a context
    warning and execution continues with the next analyzer, so a single
    flaky endpoint doesn't cost the caller everything else that succeeded.
    """

    def __init__(self, fail_fast: bool = False) -> None:
        self.fail_fast = fail_fast

    def execute(self, pipeline: list[type[BaseAnalyzer]], context: InspectContext) -> None:
        for analyzer_class in pipeline:
            analyzer = analyzer_class()
            try:
                analyzer.execute(context)
            except Exception as exc:  # noqa: BLE001 - deliberately broad: any analyzer failure
                wrapped = AnalyzerError(analyzer.name, exc)
                logger.warning("Analyzer '%s' failed: %s", analyzer.name, exc)
                context.warn(str(wrapped))
                context.events.emit(ANALYZER_FAILED, analyzer=analyzer.name, error=str(exc))
                if self.fail_fast:
                    raise wrapped from exc
