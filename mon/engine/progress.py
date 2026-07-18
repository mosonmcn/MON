"""Progress reporting -- the one deliberate exception to "analyzers never
print": this turns EventBus events into visible console output. Everything
else stays completely silent when config.response is False.
"""

from __future__ import annotations

from mon.engine.events import (
    ANALYZER_AFTER_RUN,
    ANALYZER_BEFORE_RUN,
    ANALYZER_FAILED,
    EventBus,
    INSPECTION_COMPLETED,
    INSPECTION_STARTED,
    PAGE_DOWNLOADED,
    PAGE_SKIPPED,
)

_STAGE_LABELS: dict[str, str] = {
    "crawler": "Fetching pages",
    "html": "Scanning HTML for links",
    "javascript": "Reverse-engineering JS API calls",
    "api": "Live-verifying API endpoints",
    "routes": "Building route map",
    "assets": "Saving static assets",
    "explorer": "Generating explorer map",
}


class ProgressManager:
    def __init__(self, event_bus: EventBus, enabled: bool = False) -> None:
        self.enabled = enabled
        self._pages_downloaded = 0
        if not enabled:
            return
        event_bus.subscribe(INSPECTION_STARTED, self._on_started)
        event_bus.subscribe(INSPECTION_COMPLETED, self._on_completed)
        event_bus.subscribe(ANALYZER_BEFORE_RUN, self._on_before)
        event_bus.subscribe(ANALYZER_AFTER_RUN, self._on_after)
        event_bus.subscribe(ANALYZER_FAILED, self._on_failed)
        event_bus.subscribe(PAGE_DOWNLOADED, self._on_page)
        event_bus.subscribe(PAGE_SKIPPED, self._on_skip)

    def _on_started(self, **payload: object) -> None:
        print(f"[+] Launching Ultra-Duty AI Reverse Engine for -> https://{payload.get('domain')}")

    def _on_completed(self, **payload: object) -> None:
        print("[✔ DONE] Inspection complete. Output saved.")

    def _on_before(self, **payload: object) -> None:
        name = str(payload.get("analyzer"))
        print(f"[~] {_STAGE_LABELS.get(name, name)}...")

    def _on_after(self, **payload: object) -> None:
        summary = payload.get("summary")
        if summary:
            print(f"    -> {summary}")

    def _on_failed(self, **payload: object) -> None:
        print(f"[⚠] {payload.get('analyzer')} failed: {payload.get('error')}")

    def _on_page(self, **payload: object) -> None:
        print(f"   [📥 FETCHING] -> {payload.get('path')}")

    def _on_skip(self, **payload: object) -> None:
        print(f"   [❌ FAILED] {payload.get('path')} -> HTTP {payload.get('status_code')}")
