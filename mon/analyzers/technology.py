from __future__ import annotations

import re

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_HTML, ACTION_SERVER
from mon.engine.context import InspectContext
from mon.models.technology import Technology

# (name, category, evidence_regex, confidence)
_SIGNATURES: tuple[tuple[str, str, str, int], ...] = (
    ("React", "frontend_framework", r"data-reactroot|__reactContainer|react-dom", 85),
    ("Vue.js", "frontend_framework", r"data-v-[a-f0-9]{6,}|__vue__|Vue\.createApp", 85),
    ("jQuery", "javascript_library", r"jquery(?:\.min)?\.js|jQuery\.fn\.jquery", 80),
    ("Tailwind CSS", "css_framework", r"tailwindcss|class=\"[^\"]*\b(?:flex|grid|px-\d|py-\d)\b", 60),
    ("Bootstrap", "css_framework", r"bootstrap(?:\.min)?\.css|class=\"[^\"]*\bcontainer-fluid\b", 65),
    ("WordPress", "cms", r"wp-content/|wp-includes/|/wp-json/", 90),
    ("Laravel", "backend_framework", r"laravel_session|csrf-token", 75),
    ("Next.js", "frontend_framework", r"__NEXT_DATA__|_next/static", 90),
    ("Alpine.js", "javascript_library", r"x-data=|alpinejs", 70),
    ("Axios", "javascript_library", r"\baxios\b", 60),
)


class TechnologyAnalyzer(BaseAnalyzer):
    """Signature-based technology/framework/CMS detection from HTML content
    and the server fingerprint produced by ServerAnalyzer."""

    name = "technology"
    description = "Detect frontend/backend frameworks, CMS, and libraries via signatures."
    priority = 40
    dependencies: tuple[str, ...] = (ACTION_HTML, ACTION_SERVER)

    def run(self, context: InspectContext) -> None:
        combined_html = "\n".join(page.text for page in context.html_pages())
        found: dict[str, Technology] = {}

        for name, category, pattern, confidence in _SIGNATURES:
            if re.search(pattern, combined_html, re.IGNORECASE):
                found[name] = Technology(
                    name=name, category=category, confidence=confidence,
                    evidence=f"Pattern matched in crawled HTML: /{pattern}/",
                )

        server = context.server_info
        if server:
            if server.powered_by:
                found[server.powered_by] = Technology(
                    name=server.powered_by, category="backend_language", confidence=95,
                    evidence="X-Powered-By response header",
                )
            if server.server_header:
                found.setdefault(
                    server.server_header,
                    Technology(
                        name=server.server_header, category="web_server", confidence=90,
                        evidence="Server response header",
                    ),
                )
            if any("phpsessid" in c.lower() for c in server.session_cookie_names):
                found.setdefault(
                    "PHP",
                    Technology(name="PHP", category="backend_language", confidence=85,
                               evidence="PHPSESSID cookie observed"),
                )

        context.technologies = sorted(found.values(), key=lambda t: (-t.confidence, t.name))

    def summary(self, context: InspectContext) -> str | None:
        return f"technologies {len(context.technologies)}"
