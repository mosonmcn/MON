from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Technology:
    """A single detected technology (framework, CMS, library...)."""

    name: str
    category: str
    """e.g. 'frontend_framework', 'css_framework', 'cms', 'backend_language'."""
    confidence: int
    evidence: str


@dataclass(slots=True)
class ServerInfo:
    """Backend/server fingerprint derived from response headers and cookies."""

    server_header: str | None = None
    powered_by: str | None = None
    session_cookie_names: list[str] = field(default_factory=list)
    security_headers: dict[str, str] = field(default_factory=dict)
    raw_headers: dict[str, str] = field(default_factory=dict, repr=False)
