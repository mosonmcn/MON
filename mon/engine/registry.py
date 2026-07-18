"""Analyzer registry.

The Dispatcher never has an if/elif chain keyed on action name. Every
analyzer registers itself against an action name here, once, at import
time. Adding a new analyzer means calling register_action() -- nothing in
inspector.py / resolver.py / dispatcher.py needs to change.
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


registry = AnalyzerRegistry()


def register_action(action_name: str, analyzer_class: type[BaseAnalyzer]) -> None:
    registry.register(action_name, analyzer_class)
