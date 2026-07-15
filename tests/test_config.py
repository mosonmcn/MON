from __future__ import annotations

import pytest

from mon.config import InspectConfig
from mon.exceptions import ConfigError


def test_domain_scheme_is_stripped() -> None:
    config = InspectConfig(domain="https://example.com/")
    assert config.domain == "example.com"
    assert config.base_url == "https://example.com"


def test_single_action_is_normalized_to_tuple() -> None:
    config = InspectConfig(domain="example.com", action="explorer")
    assert config.action == ("explorer",)


def test_empty_domain_raises() -> None:
    with pytest.raises(ConfigError):
        InspectConfig(domain="")


def test_unknown_action_raises() -> None:
    with pytest.raises(ConfigError):
        InspectConfig(domain="example.com", action="not_real")


def test_invalid_profile_raises() -> None:
    with pytest.raises(ConfigError):
        InspectConfig(domain="example.com", profile="ultra")


def test_max_page_all_resolves_via_profile() -> None:
    config = InspectConfig(domain="example.com", profile="fast", max_page="all")
    assert config.resolved_max_page == 15


def test_max_page_explicit_int_overrides_profile() -> None:
    config = InspectConfig(domain="example.com", profile="fast", max_page=42)
    assert config.resolved_max_page == 42
