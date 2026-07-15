"""Dependency resolver -- the "brain" of MON.

Given the actions the caller asked for (which may be composite, e.g.
``"api_spec"`` or ``"all_data"``), this module:

1. Expands composite actions into their leaf actions (`mon.constants.ACTION_GROUPS`)
2. Looks up the analyzer registered for each leaf action
3. Recursively pulls in every analyzer *that* analyzer depends on
4. Topologically sorts the result so dependencies always run before dependents

The caller never needs to know that, say, ``api_spec`` secretly requires
``html`` to run before ``javascript``, which must run before ``api``, which
must run before ``relationships`` -- that graph is entirely owned here.
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
        leaf_actions = ACTION_GROUPS.get(action, (action,))
        for leaf in leaf_actions:
            if leaf not in seen:
                seen.add(leaf)
                expanded.append(leaf)
    return expanded


def resolve_pipeline(
    requested_actions: tuple[str, ...], registry: AnalyzerRegistry
) -> list[type[BaseAnalyzer]]:
    """Return an ordered list of analyzer classes satisfying every requested
    action and all of their transitive dependencies, with dependencies always
    appearing before the analyzers that need them.

    Raises :class:`ResolverError` if an action is unknown or if two
    analyzers depend on each other (directly or transitively).
    """
    leaf_actions = _expand_composite_actions(requested_actions)

    # Recursively collect every action name that must run, including
    # transitive dependencies not explicitly requested by the caller.
    needed: set[str] = set()
    order_hint: list[str] = []

    def _collect(action_name: str, chain: tuple[str, ...]) -> None:
        if action_name in chain:
            raise ResolverError(
                f"Circular dependency detected: {' -> '.join((*chain, action_name))}"
            )
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

    # order_hint is already dependency-safe (post-order DFS), but ties
    # between independent branches are broken by each analyzer's declared
    # priority for a stable, predictable pipeline.
    analyzer_classes = [registry.get(name) for name in order_hint]
    analyzer_classes.sort(key=lambda cls: cls.priority)

    # priority-sort can reorder independent analyzers, but must never violate
    # a real dependency edge -- re-verify with a proper topological sort.
    return _stable_topological_sort(analyzer_classes)


def _stable_topological_sort(analyzer_classes: list[type[BaseAnalyzer]]) -> list[type[BaseAnalyzer]]:
    name_to_class = {cls.name: cls for cls in analyzer_classes}
    resolved: list[type[BaseAnalyzer]] = []
    resolved_names: set[str] = set()

    def visit(cls: type[BaseAnalyzer], chain: tuple[str, ...]) -> None:
        if cls.name in resolved_names:
            return
        if cls.name in chain:
            raise ResolverError(f"Circular dependency detected: {' -> '.join((*chain, cls.name))}")
        for dep_name in cls.dependencies:
            if dep_name in name_to_class:
                visit(name_to_class[dep_name], (*chain, cls.name))
        resolved.append(cls)
        resolved_names.add(cls.name)

    for cls in analyzer_classes:
        visit(cls, ())

    return resolved
