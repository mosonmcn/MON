"""Dispatcher -- runs an already-resolved pipeline of analyzer classes, in
order, against one shared InspectContext. No if/elif branching on action
names here -- that logic lives in the Resolver/Registry. This module only
instantiates, executes, handles failure, and moves on.
"""

from __future__ import annotations

import logging

from mon.analyzers.base import BaseAnalyzer
from mon.engine.context import InspectContext
from mon.engine.events import ANALYZER_FAILED
from mon.exceptions import AnalyzerError

logger = logging.getLogger("mon.engine.dispatcher")


class Dispatcher:
    """fail_fast=False (default): one analyzer failing doesn't abort the
    whole inspection -- it's recorded as a context warning, and execution
    continues, so one flaky endpoint doesn't cost everything else."""

    def __init__(self, fail_fast: bool = False) -> None:
        self.fail_fast = fail_fast

    def execute(self, pipeline: list[type[BaseAnalyzer]], context: InspectContext) -> None:
        for analyzer_class in pipeline:
            analyzer = analyzer_class()
            try:
                analyzer.execute(context)
            except Exception as exc:  # noqa: BLE001 - deliberately broad
                wrapped = AnalyzerError(analyzer.name, exc)
                logger.warning("Analyzer '%s' failed: %s", analyzer.name, exc)
                context.warn(str(wrapped))
                context.events.emit(ANALYZER_FAILED, analyzer=analyzer.name, error=str(exc))
                if self.fail_fast:
                    raise wrapped from exc
