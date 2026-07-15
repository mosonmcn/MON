from __future__ import annotations

from mon.engine.context import InspectContext
from mon.models.result import InspectResult


def build_result(context: InspectContext) -> InspectResult:
    return InspectResult(
        domain=context.config.domain,
        actions_run=tuple(sorted(context.completed_actions)),
        apis=list(context.endpoints),
        forms=list(context.forms),
        routes=list(context.routes),
        server=context.server_info,
        technology=list(context.technologies),
        explorer=context.explorer_tree,
        explorer_visual=context.explorer_visual,
        api_spec=_build_api_spec_dict(context),
        relationships=list(context.relationships),
        pages_crawled=len(context.pages),
        warnings=list(context.warnings),
    )


def _build_api_spec_dict(context: InspectContext) -> dict:
    """A flat {url: {...}} view of every endpoint, suited for direct lookup
    by URL and for tooling that expects a route-keyed specification."""
    spec: dict = {}
    for endpoint in context.endpoints:
        spec[endpoint.url] = {
            "method": endpoint.method,
            "headers": endpoint.headers,
            "payload": endpoint.payload,
            "query_parameters": endpoint.query_parameters,
            "request_schema": endpoint.request_schema,
            "response_schema": endpoint.response_schema,
            "error_schema": endpoint.error_schema,
            "authentication": endpoint.authentication,
            "csrf_token_field": endpoint.csrf_token_field,
            "uses_cookies": endpoint.uses_cookies,
            "related_html": endpoint.related_html,
            "related_javascript": endpoint.related_javascript,
            "related_form": endpoint.related_form,
            "live_verified": endpoint.live_verified,
            "confidence": {
                "score": endpoint.confidence.score,
                "reasons": endpoint.confidence.reasons,
            },
        }
    return spec
