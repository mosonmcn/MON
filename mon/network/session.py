"""Shared HTTP session.

Every network call MON makes -- crawling, live API verification, robots.txt
lookup -- goes through one :class:`SessionManager` instance per inspection.
Using a single ``requests.Session`` (instead of bare ``requests.get`` calls)
means cookies set by the server (``PHPSESSID``, ``laravel_session``, CSRF
cookies, ...) persist naturally across every request in the crawl, exactly
the way a real browser tab would behave.
"""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from mon.constants import (
    BACKOFF_FACTOR,
    DEFAULT_HEADERS,
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    RETRY_STATUS_CODES,
)


class SessionManager:
    """Owns the single :class:`requests.Session` used for one inspection run."""

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        verify_ssl: bool = True,
        max_retries: int = MAX_RETRIES,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        if extra_headers:
            self.session.headers.update(extra_headers)

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=BACKOFF_FACTOR,
            status_forcelist=RETRY_STATUS_CODES,
            allowed_methods=frozenset({"GET", "POST", "HEAD", "PUT", "DELETE", "PATCH"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("verify", self.verify_ssl)
        kwargs.setdefault("allow_redirects", True)
        return self.session.get(url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("verify", self.verify_ssl)
        kwargs.setdefault("allow_redirects", True)
        return self.session.post(url, **kwargs)

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "SessionManager":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
