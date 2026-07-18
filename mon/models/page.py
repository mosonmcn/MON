from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Page:
    """One crawled page (HTML, JS, CSS, image, ...)."""

    url: str
    path: str
    status_code: int
    content_type: str
    text: str
    headers: dict[str, str] = field(default_factory=dict)
    title: str | None = None

    @property
    def is_html(self) -> bool:
        return "text/html" in self.content_type or (
            not self.content_type and self.path.endswith((".html", "/", ""))
        )

    @property
    def is_javascript(self) -> bool:
        return "javascript" in self.content_type or self.path.endswith(".js")

    @property
    def is_static_asset(self) -> bool:
        return not self.is_html and not self.is_javascript
