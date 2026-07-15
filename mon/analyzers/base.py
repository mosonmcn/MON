"""Base class every analyzer must inherit.

Per the spec: each analyzer is a class, one analyzer class per file, and each
exposes ``name``, ``description``, ``priority``, ``dependencies``,
``before_run()``, ``run()``, and ``after_run()``. None of them call
``print()`` -- progress is communicated exclusively through
:class:`~mon.engine.context.InspectContext`'s event bus.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from mon.engine.context import InspectContext
from mon.engine.events import ANALYZER_AFTER_RUN, ANALYZER_BEFORE_RUN

logger = logging.getLogger("mon.analyzers")


class BaseAnalyzer(ABC):
    """Contract every analyzer must satisfy.

    Subclasses set ``name``/``description``/``priority``/``dependencies`` as
    class attributes and implement :meth:`run`. ``before_run``/``after_run``
    have no-op defaults and only need to be overridden when an analyzer has
    genuine setup/teardown work.
    """

    name: str = "base"
    description: str = ""
    priority: int = 100
    """Lower numbers run first among analyzers whose dependencies are already
    satisfied. This only breaks ties -- the Resolver's topological sort is
    what actually guarantees dependency order."""
    dependencies: tuple[str, ...] = ()
    """Action names (see mon.constants.LEAF_ACTIONS) this analyzer requires
    to have already run before it starts."""

    def before_run(self, context: InspectContext) -> None:  # noqa: B027 - intentional no-op default
        """Optional setup hook, called immediately before :meth:`run`."""

    @abstractmethod
    def run(self, context: InspectContext) -> None:
        """Do the analyzer's actual work, reading/writing only through ``context``."""

    def after_run(self, context: InspectContext) -> None:  # noqa: B027 - intentional no-op default
        """Optional teardown/summary hook, called immediately after :meth:`run`."""

    def summary(self, context: InspectContext) -> str | None:
        """Optional one-line human-readable summary of what this analyzer
        found (e.g. "endpoints 5"), shown by ProgressManager when
        ``response`` is truthy. Return ``None`` to show nothing special."""
        return None

    def execute(self, context: InspectContext) -> None:
        """Called by the Dispatcher. Runs the full before/run/after sequence
        and emits lifecycle events -- subclasses should not override this."""
        context.events.emit(ANALYZER_BEFORE_RUN, analyzer=self.name)
        logger.debug("Analyzer '%s' starting", self.name)

        self.before_run(context)
        self.run(context)
        self.after_run(context)

        context.completed_actions.add(self.name)
        context.events.emit(ANALYZER_AFTER_RUN, analyzer=self.name, summary=self.summary(context))
        logger.debug("Analyzer '%s' finished", self.name)
