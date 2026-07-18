from __future__ import annotations

from mon.engine.context import InspectContext
from mon.models.result import InspectResult


def build_result(context: InspectContext) -> InspectResult:
    return InspectResult(
        domain=context.config.domain,
        actions_run=tuple(sorted(context.completed_actions)),
        pages_crawled=len(context.pages),
        api_spec=_build_api_spec_dict(context),
        routes=list(context.routes),
        explorer=context.explorer_tree,
        explorer_visual=context.explorer_visual,
        assets_saved=context.assets_saved,
        warnings=list(context.warnings),
    )


def _build_api_spec_dict(context: InspectContext) -> dict:
    """Flat {url: {...}} view, matching cloner's original api_spec.json shape."""
    spec: dict = {}
    for endpoint in context.endpoints:
        spec[endpoint.url] = {
            "function_purpose": endpoint.function_purpose,
            "method": endpoint.method,
            "expected_payload_format": endpoint.expected_payload_format,
            "guessed_payload_keys": endpoint.guessed_payload_keys,
            "js_response_reading_keys": endpoint.js_response_reading_keys,
            "extracted_response_schema_from_js": endpoint.response_schema,
            "raw_js_context": endpoint.raw_js_context,
            "live_verified": endpoint.live_verified,
            "live_response_sample": endpoint.live_response_sample,
            "confidence": {
                "score": endpoint.confidence.score,
                "reasons": endpoint.confidence.reasons,
            },
        }
    return spec
