from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RelationshipChain:
    """A single reconstructed chain: HTML page -> JS file -> Form -> Endpoint.

    Any link in the chain may be ``None`` if it could not be established
    (e.g. an endpoint called from JS with no corresponding <form>).
    """

    html_page: str | None
    javascript_source: str | None
    form_id: str | None
    endpoint_url: str | None
    endpoint_method: str | None
    payload_fields: list[str] = field(default_factory=list)
    confidence: int = 0
    reasons: list[str] = field(default_factory=list)

    def describe(self) -> str:
        parts = [
            self.html_page or "?",
            self.javascript_source or "?",
            self.form_id or "?",
            f"{self.endpoint_method or '?'} {self.endpoint_url or '?'}",
        ]
        return " -> ".join(parts)
