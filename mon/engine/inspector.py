"""Inspector -- the manager.

Per the spec: *"Ba ya san HTML/JS/API/Forms. Aikinsa kawai: Receive Config,
Validate, Create Context, Resolve Actions, Execute, Return Result."* This
class deliberately knows nothing about how any individual analyzer works --
it only wires the engine components together.
"""

from __future__ import annotations

import mon.analyzers  # noqa: F401 - side effect: populates the registry
from mon.config import InspectConfig
from mon.engine.context import InspectContext
from mon.engine.dispatcher import Dispatcher
from mon.engine.events import EventBus, INSPECTION_COMPLETED, INSPECTION_FAILED, INSPECTION_STARTED
from mon.engine.output_writer import write_output
from mon.engine.progress import ProgressManager
from mon.engine.registry import registry
from mon.engine.resolver import resolve_pipeline
from mon.engine.result_builder import build_result
from mon.models.result import InspectResult
from mon.network.fetcher import Fetcher
from mon.network.session import SessionManager


class Inspector:
    def __init__(self, config: InspectConfig) -> None:
        self.config = config

    def run(self) -> InspectResult:
        events = EventBus()
        ProgressManager(events, enabled=self.config.response_enabled)

        with SessionManager(
            timeout=self.config.timeout,
            verify_ssl=self.config.verify_ssl,
        ) as session:
            fetcher = Fetcher(session)
            context = InspectContext(
                config=self.config,
                session=session,
                fetcher=fetcher,
                events=events,
            )

            events.emit(INSPECTION_STARTED, domain=self.config.domain)
            try:
                pipeline = resolve_pipeline(self.config.action, registry)
                Dispatcher().execute(pipeline, context)
            except Exception:
                events.emit(INSPECTION_FAILED, domain=self.config.domain)
                raise

            result = build_result(context)
            write_output(context, result)
            events.emit(INSPECTION_COMPLETED, domain=self.config.domain)

        return result
