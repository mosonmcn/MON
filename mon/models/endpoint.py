from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Confidence:
    """A confidence score with human-readable justification.

    Every detected object in MON that involves inference (as opposed to a
    directly-observed fact) carries one of these, per the project spec's
    "Confidence System".
    """

    score: int
    """0-100."""
    reasons: list[str] = field(default_factory=list)

    def add(self, points: int, reason: str) -> None:
        self.score = min(100, self.score + points)
        self.reasons.append(reason)


@dataclass(slots=True)
class Endpoint:
    """A fully reconstructed backend API endpoint."""

    url: str
    method: str
    headers: dict[str, str] = field(default_factory=dict)
    payload: dict = field(default_factory=dict)
    query_parameters: list[str] = field(default_factory=list)
    request_schema: dict = field(default_factory=dict)
    response_schema: dict = field(default_factory=dict)
    error_schema: dict = field(default_factory=dict)
    authentication: str | None = None
    csrf_token_field: str | None = None
    uses_cookies: bool = False

    related_html: str | None = None
    related_javascript: str | None = None
    related_form: str | None = None

    live_verified: bool = False
    live_sample_response: object | None = None

    confidence: Confidence = field(default_factory=lambda: Confidence(score=0, reasons=[]))
