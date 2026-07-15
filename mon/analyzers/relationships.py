from __future__ import annotations

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_API
from mon.engine.context import InspectContext
from mon.models.relationship import RelationshipChain


class RelationshipsAnalyzer(BaseAnalyzer):
    """Reconstructs the HTML -> JS -> Form -> Endpoint chain for every
    endpoint MON found, per the spec's "Context Intelligence" section."""

    name = "relationships"
    description = "Build the HTML -> JS -> Form -> Endpoint relationship graph."
    priority = 50
    dependencies: tuple[str, ...] = (ACTION_API,)

    def run(self, context: InspectContext) -> None:
        for endpoint in context.endpoints:
            reasons = list(endpoint.confidence.reasons)
            context.relationships.append(
                RelationshipChain(
                    html_page=endpoint.related_html,
                    javascript_source=endpoint.related_javascript,
                    form_id=endpoint.related_form,
                    endpoint_url=endpoint.url,
                    endpoint_method=endpoint.method,
                    payload_fields=sorted(endpoint.request_schema.keys()),
                    confidence=endpoint.confidence.score,
                    reasons=reasons,
                )
            )

    def summary(self, context: InspectContext) -> str | None:
        return f"relationship chains {len(context.relationships)}"
