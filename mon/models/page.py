from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Page:
    """A single fetched resource (HTML page, JS file, CSS file, or asset)."""

    url: str
    path: str
    status_code: int
    content_type: str
    text: str = field(repr=False, default="")
    title: str | None = None
    headers: dict[str, str] = field(default_factory=dict, repr=False)

    @property
    def is_html(self) -> bool:
        return "text/html" in self.content_type

    @property
    def is_javascript(self) -> bool:
        return "javascript" in self.content_type or self.path.endswith(".js")

    @property
    def is_css(self) -> bool:
        return "css" in self.content_type or self.path.endswith(".css")
