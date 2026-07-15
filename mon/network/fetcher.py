from __future__ import annotations

import logging
from dataclasses import dataclass, field

from mon.exceptions import NetworkError
from mon.network.session import SessionManager

logger = logging.getLogger("mon.network.fetcher")


@dataclass(slots=True)
class FetchResponse:
    """Typed result of a single HTTP GET, replacing the old bare tuple return
    (``status, content, ctype``) that made call sites fragile -- callers now
    get named attributes and cannot accidentally unpack the wrong arity."""

    url: str
    status_code: int
    text: str
    content_type: str
    headers: dict[str, str] = field(default_factory=dict, repr=False)
    ok: bool = field(init=False)

    def __post_init__(self) -> None:
        self.ok = 200 <= self.status_code < 300


class Fetcher:
    """High-level fetch operation used by every analyzer that needs the network."""

    def __init__(self, session: SessionManager) -> None:
        self._session = session

    def get(self, url: str) -> FetchResponse:
        try:
            response = self._session.get(url)
        except Exception as exc:  # noqa: BLE001 - we deliberately normalize all network errors
            raise NetworkError(f"GET {url} failed: {exc}") from exc

        content_type = response.headers.get("Content-Type", "").lower()
        return FetchResponse(
            url=url,
            status_code=response.status_code,
            text=response.text,
            content_type=content_type,
            headers=dict(response.headers),
        )

    def post(self, url: str, *, json: dict | None = None, data: dict | None = None) -> FetchResponse:
        try:
            response = self._session.post(url, json=json, data=data)
        except Exception as exc:  # noqa: BLE001
            raise NetworkError(f"POST {url} failed: {exc}") from exc

        content_type = response.headers.get("Content-Type", "").lower()
        return FetchResponse(
            url=url,
            status_code=response.status_code,
            text=response.text,
            content_type=content_type,
            headers=dict(response.headers),
        )
