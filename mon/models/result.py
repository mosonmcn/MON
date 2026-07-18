from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class InspectResult:
    """Everything a single ``mon.inspect(...)`` call produced."""

    domain: str
    actions_run: tuple[str, ...]
    pages_crawled: int
    api_spec: dict = field(default_factory=dict)
    routes: list = field(default_factory=list)
    explorer: dict = field(default_factory=dict)
    explorer_visual: str = ""
    assets_saved: int = 0
    warnings: list[str] = field(default_factory=list)
