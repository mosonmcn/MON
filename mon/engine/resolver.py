"""Dependency resolver -- expands composite actions, pulls in transitive
analyzer dependencies, and topologically sorts the result so dependencies
always run before dependents. The caller never needs to know that
'api_spec' secretly requires html to run before javascript, which must run
before api -- that graph is entirely owned here.
"""

from __future__ import annotations

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_GROUPS
from mon.engine.registry import AnalyzerRegistry
from mon.exceptions import ResolverError


def _expand_composite_actions(requested: tuple[str, ...]) -> list[str]:
    expanded: list[str] = []
    seen: set[str] = set()
    for action in requested:
        for leaf in ACTION_GROUPS.get(action, (action,)):
            if leaf not in seen:
                seen.add(leaf)
                expanded.append(leaf)
    return expanded


def resolve_pipeline(
    requested_actions: tuple[str, ...], registry: AnalyzerRegistry
) -> list[type[BaseAnalyzer]]:
    leaf_actions = _expand_composite_actions(requested_actions)

    needed: set[str] = set()
    order_hint: list[str] = []

    def _collect(action_name: str, chain: tuple[str, ...]) -> None:
        if action_name in chain:
            raise ResolverError(f"Circular dependency: {' -> '.join((*chain, action_name))}")
        if action_name in needed:
            return
        if not registry.has(action_name):
            raise ResolverError(
                f"Unknown action '{action_name}'. Registered actions: {registry.all_actions()}"
            )
        analyzer_class = registry.get(action_name)
        for dep in analyzer_class.dependencies:
            _collect(dep, (*chain, action_name))
        needed.add(action_name)
        order_hint.append(action_name)

    for action in leaf_actions:
        _collect(action, ())

    analyzer_classes = [registry.get(name) for name in order_hint]
    analyzer_classes.sort(key=lambda cls: cls.priority)
    return _stable_topological_sort(analyzer_classes)


def _stable_topological_sort(analyzer_classes: list[type[BaseAnalyzer]]) -> list[type[BaseAnalyzer]]:
    name_to_class = {cls.name: cls for cls in analyzer_classes}
    resolved: list[type[BaseAnalyzer]] = []
    resolved_names: set[str] = set()

    def visit(cls: type[BaseAnalyzer], chain: tuple[str, ...]) -> None:
        if cls.name in resolved_names:
            return
        if cls.name in chain:
            raise ResolverError(f"Circular dependency: {' -> '.join((*chain, cls.name))}")
        for dep_name in cls.dependencies:
            if dep_name in name_to_class:
                visit(name_to_class[dep_name], (*chain, cls.name))
        resolved.append(cls)
        resolved_names.add(cls.name)

    for cls in analyzer_classes:
        visit(cls, ())
    return resolved
