"""Progress reporting.

Per the spec: *"Ba modules ne suke yin print ba"* (modules never print) --
that rule is about ANALYZERS, which stay completely silent and only emit
events. ProgressManager is the one deliberate exception: its entire job is
turning those events into visible output for the person running the
inspection, so it prints directly rather than going through Python's
``logging`` module (which is silent unless the caller has configured a
handler/level themselves -- a footgun for something meant to give live,
no-setup-required feedback).
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
    "crawler": "Crawling",
    "html": "Parsing HTML",
    "javascript": "Analyzing JavaScript",
    "forms": "Analyzing forms",
    "api": "Reconstructing API endpoints",
    "routes": "Building route map",
    "assets": "Cataloguing assets",
    "metadata": "Extracting metadata",
    "technology": "Fingerprinting technology",
    "server_info": "Inspecting server",
    "relationships": "Building relationship graph",
    "explorer": "Generating explorer",
}


class ProgressManager:
    """Attaches live, human-readable console output to an :class:`EventBus`.

    Only active when ``enabled=True`` (wired to ``InspectConfig.response`` in
    the SDK) -- when disabled, nothing subscribes and the whole inspection
    runs completely silently, exactly like calling a library should.
    """

    def __init__(self, event_bus: EventBus, enabled: bool = False) -> None:
        self.enabled = enabled
        self._pages_downloaded = 0
        if not enabled:
            return

        event_bus.subscribe(INSPECTION_STARTED, self._on_inspection_started)
        event_bus.subscribe(INSPECTION_COMPLETED, self._on_inspection_completed)
        event_bus.subscribe(ANALYZER_BEFORE_RUN, self._on_analyzer_before_run)
        event_bus.subscribe(ANALYZER_AFTER_RUN, self._on_analyzer_after_run)
        event_bus.subscribe(ANALYZER_FAILED, self._on_analyzer_failed)
        event_bus.subscribe(PAGE_DOWNLOADED, self._on_page_downloaded)
        event_bus.subscribe(PAGE_SKIPPED, self._on_page_skipped)

    def _on_inspection_started(self, **payload: object) -> None:
        print(f"[MON] Inspecting {payload.get('domain')} ...", flush=True)

    def _on_inspection_completed(self, **payload: object) -> None:
        print("[MON] Done. Output saved.", flush=True)

    def _on_analyzer_before_run(self, **payload: object) -> None:
        name = str(payload.get("analyzer"))
        print(f"[MON] {_STAGE_LABELS.get(name, name)}...", flush=True)

    def _on_analyzer_after_run(self, **payload: object) -> None:
        name = str(payload.get("analyzer"))
        summary = payload.get("summary")
        if summary:
            print(f"[MON]   -> {summary}", flush=True)
        else:
            print(f"[MON]   -> {name} done", flush=True)

    def _on_analyzer_failed(self, **payload: object) -> None:
        print(f"[MON] ⚠ {payload.get('analyzer')} failed: {payload.get('error')}", flush=True)

    def _on_page_downloaded(self, **payload: object) -> None:
        self._pages_downloaded += 1
        if self._pages_downloaded % 5 == 0:
            print(f"[MON]   ... {self._pages_downloaded} pages downloaded so far", flush=True)

    def _on_page_skipped(self, **payload: object) -> None:
        print(f"[MON]   skipped {payload.get('path')} (status={payload.get('status_code')})", flush=True)
