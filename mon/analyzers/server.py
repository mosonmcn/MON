from __future__ import annotations

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_CRAWLER, ACTION_SERVER
from mon.engine.context import InspectContext
from mon.models.technology import ServerInfo

_SESSION_COOKIE_PATTERNS = (
    "phpsessid", "laravel_session", "connect.sid", "jsessionid",
    "asp.net_sessionid", "csrftoken", "xsrf-token", "_session",
)
_SECURITY_HEADER_NAMES = (
    "content-security-policy", "strict-transport-security", "x-frame-options",
    "x-content-type-options", "referrer-policy", "permissions-policy",
)


class ServerAnalyzer(BaseAnalyzer):
    """Fingerprints the backend server from response headers and cookie names."""

    name = ACTION_SERVER
    description = "Fingerprint server/backend from response headers and cookies."
    priority = 20
    dependencies: tuple[str, ...] = (ACTION_CRAWLER,)

    def run(self, context: InspectContext) -> None:
        homepage = context.pages.get("/")
        reference_page = homepage or next(iter(context.pages.values()), None)
        if reference_page is None:
            return

        headers = {k.lower(): v for k, v in reference_page.headers.items()}

        session_cookie_names = []
        for raw_cookie in context.session.session.cookies:
            name_lower = raw_cookie.name.lower()
            if any(pattern in name_lower for pattern in _SESSION_COOKIE_PATTERNS):
                session_cookie_names.append(raw_cookie.name)

        context.server_info = ServerInfo(
            server_header=headers.get("server"),
            powered_by=headers.get("x-powered-by"),
            session_cookie_names=sorted(set(session_cookie_names)),
            security_headers={h: headers[h] for h in _SECURITY_HEADER_NAMES if h in headers},
            raw_headers=reference_page.headers,
        )

    def summary(self, context: InspectContext) -> str | None:
        return "server fingerprint captured" if context.server_info else "no server info"
