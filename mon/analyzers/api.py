"""ApiAnalyzer -- builds Endpoint objects from context.raw_api_spec
(JavascriptAnalyzer's output) and, when the profile enables it, live-
verifies each one against the real server.

Live verification is CLONER'S ORIGINAL api_verifier.py logic
(live_sniff_response), ported to use context.fetcher.post/get instead of
bare requests calls, so it still goes through the same fetch path as
everything else while keeping cloner's exact mock-payload heuristics.
"""

from __future__ import annotations

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_API, ACTION_CRAWLER, ACTION_JAVASCRIPT
from mon.engine.context import InspectContext
from mon.models.endpoint import Confidence, Endpoint


def _build_mock_payload(method: str, payload_keys: list[str]) -> dict:
    """Cloner's original mock payload heuristic from api_verifier.py."""
    mock_payload: dict = {}
    if method.upper() == "POST" and payload_keys:
        for key in payload_keys:
            lowered = key.lower()
            if "id" in lowered or "number" in lowered or "bvn" in lowered or "nin" in lowered:
                mock_payload[key] = "1234567890"
            elif "amount" in lowered or "price" in lowered or "balance" in lowered:
                mock_payload[key] = 1000
            else:
                mock_payload[key] = "test_data"
    return mock_payload


def _live_sniff_response(context: InspectContext, route: str, method: str, payload_keys: list[str]):
    """Cloner's live_sniff_response, using context.fetcher (same headers/
    timeout family) instead of a bare requests call."""
    base_url = context.config.base_url
    if not route.startswith("http"):
        if base_url.endswith("/") and route.startswith("/"):
            full_url = base_url + route[1:]
        elif not base_url.endswith("/") and not route.startswith("/"):
            full_url = base_url + "/" + route
        else:
            full_url = base_url + route
    else:
        full_url = route

    mock_payload = _build_mock_payload(method, payload_keys)

    if method.upper() == "POST":
        response = context.fetcher.post(full_url, json=mock_payload)
    else:
        response = context.fetcher.get(full_url)

    ctype = response.content_type
    if "application/json" in ctype or "text/json" in ctype:
        try:
            import json
            json_data = json.loads(response.text)
            if isinstance(json_data, list) and len(json_data) > 0:
                return json_data[0], ctype
            return json_data, ctype
        except Exception:
            return {"error": "Failed to parse returned JSON string"}, ctype
    else:
        return {"raw_non_json_sample": response.text[:200]}, ctype


class ApiAnalyzer(BaseAnalyzer):
    name = ACTION_API
    description = "Builds Endpoint objects from JS static analysis, optionally live-verified."
    priority = 30
    dependencies: tuple[str, ...] = (ACTION_CRAWLER, ACTION_JAVASCRIPT)

    def run(self, context: InspectContext) -> None:
        live_verify = context.config.live_verify_enabled

        for route, spec in context.raw_api_spec.items():
            reasons = ["Discovered via static JS analysis (apiCall/fetch call site)"]
            score = 40
            if spec.get("guessed_payload_keys"):
                reasons.append("Payload keys matched from FormData/JSON body")
                score += 15
            if spec.get("js_response_reading_keys"):
                reasons.append("Success/error branches detected in JS")
                score += 15

            endpoint = Endpoint(
                url=route,
                method=spec.get("method", "GET"),
                function_purpose=spec.get("function_purpose", "unknown_function"),
                expected_payload_format=spec.get("expected_payload_format", "Raw JSON (application/json)"),
                guessed_payload_keys=spec.get("guessed_payload_keys", []),
                js_response_reading_keys=spec.get("js_response_reading_keys", []),
                response_schema=spec.get("extracted_response_schema_from_js", {}),
                raw_js_context=spec.get("raw_js_context", ""),
            )

            if live_verify:
                sample, ctype = _live_sniff_response(
                    context, route, endpoint.method, endpoint.guessed_payload_keys
                )
                endpoint.live_verified = "connection_error" not in sample
                endpoint.live_response_sample = sample
                endpoint.live_content_type = ctype
                if endpoint.live_verified:
                    reasons.append("Live-verified against server")
                    score += 20

            endpoint.confidence = Confidence(score=min(score, 100), reasons=reasons)
            context.endpoints.append(endpoint)

    def summary(self, context: InspectContext) -> str | None:
        verified = sum(1 for e in context.endpoints if e.live_verified)
        return f"endpoints {len(context.endpoints)} (live-verified {verified})"
