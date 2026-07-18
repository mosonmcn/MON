from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Route:
    """One entry in the explorer / route map (a frontend page or a
    discovered backend endpoint)."""

    path: str
    file: str
    type: str
    format: str = ""
    title: str | None = None
