from __future__ import annotations

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_HTML, ACTION_JAVASCRIPT
from mon.engine.context import InspectContext
from mon.models.script import ApiCallSite
from mon.parsers import js_parser as jp
from mon.parsers.url_utils import resolve_api_path


class JavascriptAnalyzer(BaseAnalyzer):
    """Finds every outbound API call inside every script -- both standalone
    external JS files and inline <script> blocks -- across every call style
    MON recognizes, and reconstructs its request/response shape via
    branch-splitting and name-agnostic variable detection.
    """

    name = ACTION_JAVASCRIPT
    description = "Detect API call sites and reconstruct request/response schemas from JS."
    priority = 30
    dependencies: tuple[str, ...] = (ACTION_HTML,)

    def run(self, context: InspectContext) -> None:
        # External JS files: analyzed directly from context.pages, keyed by
        # their own crawled path. This does not depend on matching a
        # <script src="..."> attribute value against anything -- a page that
        # was successfully crawled and classified as JavaScript is analyzed
        # regardless of how it was linked to (absolute path, relative path,
        # or a different host entirely resolved during crawling).
        for page in context.javascript_pages():
            self._analyze_source(context, js_content=page.text, current_file_route=page.path,
                                  page_url=page.url, script_src=page.path)

        # Inline <script> blocks: analyzed from their captured content,
        # scoped to the page that embeds them.
        for script in context.scripts:
            if not script.inline or not script.content:
                continue
            page = next((p for p in context.pages.values() if p.url == script.page_url), None)
            route = page.path if page else "/"
            self._analyze_source(context, js_content=script.content, current_file_route=route,
                                  page_url=script.page_url, script_src=None)

    def _analyze_source(self, context: InspectContext, js_content: str, current_file_route: str,
                         page_url: str, script_src: str | None) -> None:
        base_api_url = jp.detect_base_api_url(js_content)
        payload_format = jp.detect_payload_format(js_content)

        for call in jp.find_call_sites(js_content):
            full_route = resolve_api_path(current_file_route, base_api_url, call.endpoint_path)

            snippet = jp.extract_function_snippet(js_content, call.match_index)
            function_body = snippet.code if snippet.method == "function_boundary" else js_content

            payload_keys = jp.extract_payload_keys(function_body)
            branches = jp.split_success_error_branches(function_body)
            response_vars = jp.detect_response_variable_names(function_body)
            dotted_pattern = jp.build_dotted_path_pattern(response_vars)
            success_schema = jp.build_schema(branches.success_branch, dotted_pattern)
            error_schema = (
                jp.build_schema(branches.error_branch, dotted_pattern) if branches.error_branch else {}
            )

            context.api_call_sites.append(
                ApiCallSite(
                    page_url=page_url,
                    script_src=script_src,
                    endpoint_path=full_route,
                    http_method=call.http_method,
                    call_style=call.call_style,
                    wrapper_function_name=call.wrapper_function_name,
                    response_variable_names=sorted(response_vars),
                    payload_keys=payload_keys,
                    payload_format=payload_format,
                    success_schema=success_schema,
                    error_schema=error_schema,
                    branch_split_detected=branches.detected,
                    raw_context=function_body[:400],
                )
            )

    def summary(self, context: InspectContext) -> str | None:
        return f"API call sites {len(context.api_call_sites)}"
