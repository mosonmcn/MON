from __future__ import annotations

import time

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_CRAWLER
from mon.engine.context import InspectContext
from mon.engine.events import PAGE_DOWNLOADED, PAGE_SKIPPED
from mon.models.page import Page
from mon.network.robots import discover_seed_paths
from mon.parsers import js_parser as jp
from mon.parsers.html_parser import HTMLDocument


class CrawlerAnalyzer(BaseAnalyzer):
    """Breadth-first crawl of the target domain.

    Discovers new pages from two independent sources: standard HTML
    attributes (<a href>, <link href>, <script src>, ...) and client-side
    navigation calls inside JavaScript (window.location assignments, SPA
    router push/replace, history.pushState/replaceState). The second source
    matters because many applications redirect the user to a route (e.g.
    /dashboard after a successful login) purely at runtime, with no
    corresponding <a href> anywhere in the markup -- a crawler relying on
    HTML links alone would never find that route at all.

    Every other analyzer depends on this one (directly or transitively) --
    it is the only analyzer with no dependencies of its own, and the only
    one that touches the network for page discovery.
    """

    name = ACTION_CRAWLER
    description = "Breadth-first crawl of same-domain pages, respecting max_page/profile."
    priority = 0
    dependencies: tuple[str, ...] = ()

    def run(self, context: InspectContext) -> None:
        config = context.config
        base_url = config.base_url
        domain = config.domain
        max_page = config.resolved_max_page
        delay = config.delay_seconds

        context.queue = ["/"]
        try:
            context.queue.extend(
                p for p in discover_seed_paths(base_url, context.fetcher) if p not in context.queue
            )
        except Exception as exc:  # noqa: BLE001 - robots.txt discovery is best-effort only
            context.warn(f"robots.txt/sitemap discovery failed: {exc}")

        pages_done = 0
        while context.queue and pages_done < max_page:
            path = context.queue.pop(0)
            if path in context.visited:
                continue
            context.visited.add(path)

            if delay:
                time.sleep(delay)

            full_url = base_url.rstrip("/") + path
            response = context.fetcher.get(full_url)

            if not response.ok:
                context.events.emit(
                    PAGE_SKIPPED, path=path, status_code=response.status_code
                )
                continue

            pages_done += 1
            page = Page(
                url=full_url,
                path=path,
                status_code=response.status_code,
                content_type=response.content_type,
                text=response.text,
                headers=response.headers,
            )

            if page.is_html:
                doc = HTMLDocument(response.text, full_url, domain)
                page.title = doc.title
                for new_path in doc.discovered_links():
                    self._enqueue(context, new_path)

                for raw_script in doc.scripts():
                    if raw_script.inline and raw_script.content:
                        for nav_path in jp.find_navigation_targets(raw_script.content):
                            self._enqueue(context, nav_path)

            elif page.is_javascript:
                for nav_path in jp.find_navigation_targets(response.text):
                    self._enqueue(context, nav_path)

            context.pages[path] = page
            context.events.emit(PAGE_DOWNLOADED, path=path, status_code=response.status_code)

    @staticmethod
    def _enqueue(context: InspectContext, path: str) -> None:
        if path not in context.visited and path not in context.queue:
            context.queue.append(path)

    def summary(self, context: InspectContext) -> str | None:
        return f"pages {len(context.pages)}"
