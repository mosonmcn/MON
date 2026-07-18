from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Confidence:
    score: int = 0
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Endpoint:
    """One reconstructed backend API endpoint, built from cloner's JS static
    analysis (mon.parsers.js_api_parser) and, when live_verify is on,
    confirmed against the real server (mon.network.fetcher.Fetcher.post/get)."""

    url: str
    method: str
    function_purpose: str = "unknown_function"
    expected_payload_format: str = "Raw JSON (application/json)"
    guessed_payload_keys: list[str] = field(default_factory=list)
    js_response_reading_keys: list[str] = field(default_factory=list)
    response_schema: dict = field(default_factory=dict)
    raw_js_context: str = ""
    live_verified: bool = False
    live_response_sample: dict | None = None
    live_content_type: str | None = None
    confidence: Confidence = field(default_factory=Confidence)
