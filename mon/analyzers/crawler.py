"""Breadth-first crawl of the target domain -- THIS IS CLONER'S ORIGINAL
main.py while-loop, moved into MON's analyzer shape.

Every network call in this analyzer goes through ``context.fetcher.get()``,
which is cloner's original fetcher.py (plain requests.get, cloner's
mobile-Chrome headers, 10s timeout, no session/cookies/retries). Nothing
about *how a page is fetched* changed -- only *where the loop lives*
changed, from a bare while-loop in main.py to run() on this analyzer.

Every other analyzer depends on this one (directly or transitively) -- it
is the only analyzer with no dependencies, and the only one that touches
the network for page discovery.
"""

from __future__ import annotations

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_CRAWLER
from mon.engine.context import InspectContext
from mon.engine.events import PAGE_DOWNLOADED, PAGE_SKIPPED
from mon.models.page import Page
from mon.parsers.link_parser import extract_paths


class CrawlerAnalyzer(BaseAnalyzer):
    name = ACTION_CRAWLER
    description = "Breadth-first same-domain crawl using cloner's original fetch() logic."
    priority = 0
    dependencies: tuple[str, ...] = ()

    def run(self, context: InspectContext) -> None:
        config = context.config
        base_url = config.base_url
        domain = config.domain
        max_page = config.resolved_max_page

        # visited/queue live on context so later analyzers (html) can see
        # discovered_links without re-crawling -- but the crawl itself is
        # cloner's original: pop from front, fetch, parse links, extend queue.
        context.queue = ["/"]
        pages_done = 0

        while context.queue and pages_done < max_page:
            path = context.queue.pop(0)
            if path in context.visited:
                continue
            context.visited.add(path)

            full_url = base_url.rstrip("/") + path
            response = context.fetcher.get(full_url)  # cloner's fetch(), unchanged

            if not response.ok:
                context.events.emit(PAGE_SKIPPED, path=full_url, status_code=response.status_code)
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
            context.pages[path] = page
            context.events.emit(PAGE_DOWNLOADED, path=full_url, status_code=response.status_code)

            # Cloner's universal link scanner -- discover new same-domain
            # paths from HTML links and JS router strings, feed them back
            # into the queue so the crawl keeps expanding.
            new_paths = extract_paths(response.text, full_url, domain)
            context.discovered_links[path] = set(new_paths)
            for new_path in new_paths:
                if new_path not in context.visited and new_path not in context.queue:
                    context.queue.append(new_path)

    def summary(self, context: InspectContext) -> str | None:
        return f"pages {len(context.pages)}"
