from __future__ import annotations

from urllib.parse import urljoin

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_FORMS, ACTION_JAVASCRIPT
from mon.engine.context import InspectContext
from mon.exceptions import NetworkError
from mon.models.endpoint import Confidence, Endpoint
from mon.models.form import Form
from mon.models.script import ApiCallSite

_MOCK_VALUES_BY_KEY_HINT: dict[str, str] = {
    "email": "test@example.com",
    "phone": "08010000000",
    "amount": "100",
    "password": "Password123!",
    "username": "testuser",
    "token": "sample-token",
}


def _mock_value_for(key: str) -> str:
    lower = key.lower()
    for hint, value in _MOCK_VALUES_BY_KEY_HINT.items():
        if hint in lower:
            return value
    return "sample_value"


class ApiAnalyzer(BaseAnalyzer):
    """Reconstructs full :class:`~mon.models.endpoint.Endpoint` objects from
    JS call sites, cross-referenced against forms, and optionally live-
    verified against the real server (profile-dependent).
    """

    name = "api"
    description = "Reconstruct endpoints from JS call sites, cross-referenced with forms."
    priority = 40
    dependencies: tuple[str, ...] = (ACTION_JAVASCRIPT, ACTION_FORMS)

    def run(self, context: InspectContext) -> None:
        merged: dict[tuple[str, str], Endpoint] = {}

        for call in context.api_call_sites:
            key = (call.endpoint_path, call.http_method)
            endpoint = merged.get(key)
            if endpoint is None:
                endpoint = self._build_endpoint(call)
                merged[key] = endpoint
            else:
                self._merge_into(endpoint, call)

        for endpoint in merged.values():
            matching_form = self._match_form(endpoint, context.forms)
            if matching_form:
                endpoint.related_form = matching_form.id or matching_form.action
                for field_name in matching_form.field_names:
                    if field_name not in endpoint.request_schema:
                        endpoint.request_schema[field_name] = "TYPE_UNKNOWN"
                endpoint.confidence.add(15, f"Matched to HTML form '{matching_form.action}'")

            if context.config.live_verify_enabled:
                self._live_verify(context, endpoint)

        context.endpoints = list(merged.values())

    # ------------------------------------------------------------------ #

    def _build_endpoint(self, call: ApiCallSite) -> Endpoint:
        confidence = Confidence(score=0, reasons=[])
        confidence.add(40, f"Detected via {call.call_style} call in JavaScript")
        if call.branch_split_detected:
            confidence.add(15, "Success/error branches detected in JS")
        if call.payload_keys:
            confidence.add(10, "Payload keys extracted from JS")
        if call.response_variable_names:
            confidence.add(10, "Response variable identified in JS (name-agnostic detection)")

        return Endpoint(
            url=call.endpoint_path,
            method=call.http_method,
            request_schema={k: "TYPE_UNKNOWN" for k in call.payload_keys},
            response_schema=call.success_schema,
            error_schema=call.error_schema,
            related_html=call.page_url,
            related_javascript=call.script_src or call.page_url,
            confidence=confidence,
        )

    def _merge_into(self, endpoint: Endpoint, call: ApiCallSite) -> None:
        for k in call.payload_keys:
            endpoint.request_schema.setdefault(k, "TYPE_UNKNOWN")
        endpoint.response_schema = {**call.success_schema, **endpoint.response_schema}
        endpoint.error_schema = {**call.error_schema, **endpoint.error_schema}

    @staticmethod
    def _match_form(endpoint: Endpoint, forms: list[Form]) -> Form | None:
        for form in forms:
            action_path = form.action.split("?")[0]
            if action_path and (action_path in endpoint.url or endpoint.url in action_path):
                return form
        return None

    def _live_verify(self, context: InspectContext, endpoint: Endpoint) -> None:
        if endpoint.method not in ("POST", "PUT", "PATCH", "GET"):
            return

        full_url = urljoin(context.config.base_url, endpoint.url)
        mock_payload = {k: _mock_value_for(k) for k in endpoint.request_schema}

        try:
            if endpoint.method == "GET":
                response = context.fetcher.get(full_url)
            else:
                # Try JSON first; many modern APIs expect it.
                response = context.fetcher.post(full_url, json=mock_payload)
                if response.status_code in (400, 415, 422) and mock_payload:
                    # Fall back to application/x-www-form-urlencoded -- common
                    # for classic PHP backends reading $_POST directly.
                    response = context.fetcher.post(full_url, data=mock_payload)
        except NetworkError as exc:
            context.warn(f"Live verification failed for {endpoint.url}: {exc}")
            return

        endpoint.live_verified = True
        endpoint.payload = mock_payload
        if "json" in response.content_type:
            try:
                import json
                endpoint.live_sample_response = json.loads(response.text)
            except ValueError:
                endpoint.live_sample_response = response.text[:500]
        else:
            endpoint.live_sample_response = response.text[:500]

        endpoint.confidence.add(20, f"Live-verified against server (HTTP {response.status_code})")

    def summary(self, context: InspectContext) -> str | None:
        return f"endpoints {len(context.endpoints)}"
