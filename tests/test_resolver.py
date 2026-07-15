from __future__ import annotations

import pytest

import mon.analyzers  # noqa: F401 - populates the registry
from mon.constants import ACTION_ALL_DATA, ACTION_API_SPEC
from mon.engine.registry import registry
from mon.engine.resolver import resolve_pipeline
from mon.exceptions import ResolverError


def test_resolve_single_leaf_action_has_no_dependencies_missing() -> None:
    pipeline = resolve_pipeline(("crawler",), registry)
    names = [cls.name for cls in pipeline]
    assert names == ["crawler"]


def test_resolve_api_spec_orders_dependencies_before_dependents() -> None:
    pipeline = resolve_pipeline((ACTION_API_SPEC,), registry)
    names = [cls.name for cls in pipeline]

    assert names.index("crawler") < names.index("html")
    assert names.index("html") < names.index("javascript")
    assert names.index("javascript") < names.index("api")
    assert names.index("forms") < names.index("api")
    assert names.index("api") < names.index("relationships")


def test_resolve_all_data_includes_every_leaf_action() -> None:
    pipeline = resolve_pipeline((ACTION_ALL_DATA,), registry)
    names = {cls.name for cls in pipeline}
    assert names == set(registry.all_actions())


def test_resolve_unknown_action_raises() -> None:
    with pytest.raises(ResolverError):
        resolve_pipeline(("definitely_not_a_real_action",), registry)


def test_resolve_is_idempotent_for_duplicate_requests() -> None:
    pipeline = resolve_pipeline(("api", "api"), registry)
    names = [cls.name for cls in pipeline]
    assert names.count("api") == 1
