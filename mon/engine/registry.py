"""Analyzer registry.

The Dispatcher never has an ``if action == "api": ... elif action == "forms":
...`` chain. Instead every analyzer registers itself against an action name
here, once, at import time. Adding a new analyzer (e.g. a future
``GraphQLAnalyzer``) means calling :func:`register_action` -- nothing in
:mod:`mon.engine.inspector`, :mod:`mon.engine.resolver`, or
:mod:`mon.engine.dispatcher` needs to change.
"""

from __future__ import annotations

from mon.analyzers.base import BaseAnalyzer
from mon.exceptions import RegistryError


class AnalyzerRegistry:
    def __init__(self) -> None:
        self._analyzers: dict[str, type[BaseAnalyzer]] = {}

    def register(self, action_name: str, analyzer_class: type[BaseAnalyzer]) -> None:
        self._analyzers[action_name] = analyzer_class

    def get(self, action_name: str) -> type[BaseAnalyzer]:
        try:
            return self._analyzers[action_name]
        except KeyError as exc:
            raise RegistryError(
                f"No analyzer registered for action '{action_name}'. "
                f"Registered actions: {sorted(self._analyzers)}"
            ) from exc

    def has(self, action_name: str) -> bool:
        return action_name in self._analyzers

    def all_actions(self) -> list[str]:
        return sorted(self._analyzers)


# One process-wide registry. Analyzer modules call register_action() at
# import time (see mon/analyzers/__init__.py), so simply importing
# mon.analyzers is enough to populate this before the resolver/dispatcher
# ever need it.
registry = AnalyzerRegistry()


def register_action(action_name: str, analyzer_class: type[BaseAnalyzer]) -> None:
    registry.register(action_name, analyzer_class)
