from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Route:
    """A single entry in the frontend route map (produced by RoutesAnalyzer)."""

    path: str
    file: str
    type: str
    title: str | None = None
    is_directory: bool = False
