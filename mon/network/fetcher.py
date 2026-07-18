"""Website access layer -- THIS IS CLONER'S ORIGINAL LOGIC, not MON's.

The rest of this project was rebuilt to follow MON's modular architecture
(config / engine / analyzers / exporters), but the one thing that stays
100% cloner is *how a page actually gets fetched*: plain ``requests.get``
per call, cloner's own mobile-Chrome ``User-Agent``/header set, a bare
10-second timeout, and a (status, text, content_type) return shape -- no
shared ``requests.Session``, no automatic retries, no cookie jar carried
between calls. That was the explicit ask: keep cloner's network access,
adopt MON's structure everywhere else.

Only the wrapping changed: it now returns a small ``FetchResponse`` object
instead of a bare tuple, purely so the rest of the engine (which follows
MON's typed-response convention) can call ``response.ok`` /
``response.status_code`` / ``response.text`` like it does for every other
analyzer, without every call site unpacking a 3-tuple.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import requests

# Cloner's original headers, verbatim.
HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/117.0.0.0 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}


@dataclass(slots=True)
class FetchResponse:
    """Typed wrapper around cloner's (status, text, content_type) tuple."""

    url: str
    status_code: int
    text: str
    content_type: str
    headers: dict[str, str] = field(default_factory=dict, repr=False)
    ok: bool = field(init=False)

    def __post_init__(self) -> None:
        self.ok = self.status_code == 200


class Fetcher:
    """Thin class wrapper around cloner's original ``fetch()`` function, so
    analyzers can depend on an object (``context.fetcher``) the same way
    they would with MON's own network layer -- while every request under
    the hood still behaves exactly like cloner's fetcher.py did."""

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    def get(self, url: str) -> FetchResponse:
        """Yana kwaso shafukan yanar gizo kuma yana dawo da Status Code,
        Danyen Rubutu (HTML/JS), da kuma Content-Type -- exactly like
        cloner's original ``fetch()``."""
        try:
            r = requests.get(url, headers=HEADERS, timeout=self.timeout)
            content_type = r.headers.get("Content-Type", "").lower()
            return FetchResponse(
                url=url,
                status_code=r.status_code,
                text=r.text,
                content_type=content_type,
                headers=dict(r.headers),
            )
        except Exception as exc:  # noqa: BLE001 - cloner swallows all fetch errors as a failed response
            return FetchResponse(url=url, status_code=500, text=str(exc), content_type="failed")

    def post(self, url: str, *, json: dict | None = None, headers: dict | None = None,
             timeout: int | None = None) -> FetchResponse:
        """Used by the API live-verifier (cloner's api_verifier.py logic),
        which needs POST support that the original fetch() never had."""
        req_headers = headers or {
            "User-Agent": HEADERS["User-Agent"],
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
        }
        try:
            r = requests.post(url, json=json, headers=req_headers, timeout=timeout or 5)
            content_type = r.headers.get("Content-Type", "").lower()
            return FetchResponse(
                url=url, status_code=r.status_code, text=r.text,
                content_type=content_type, headers=dict(r.headers),
            )
        except Exception as exc:  # noqa: BLE001
            return FetchResponse(url=url, status_code=500, text=str(exc), content_type="failed")
