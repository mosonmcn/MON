from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ScriptRef:
    """A single <script> tag (inline or external) discovered on a page."""

    page_url: str
    src: str | None
    inline: bool
    content: str = field(repr=False, default="")


@dataclass(slots=True)
class ApiCallSite:
    """A single API call detected inside JavaScript source, before it has been
    promoted to a full :class:`~mon.models.endpoint.Endpoint` by ApiAnalyzer.
    """

    page_url: str
    script_src: str | None
    endpoint_path: str
    http_method: str
    call_style: str
    """One of: 'fetch', 'axios', 'xhr', 'jquery_ajax', 'ky', 'superagent', 'custom_wrapper'."""
    wrapper_function_name: str
    response_variable_names: list[str] = field(default_factory=list)
    payload_keys: list[str] = field(default_factory=list)
    payload_format: str = "Raw JSON (application/json)"
    success_schema: dict = field(default_factory=dict)
    error_schema: dict = field(default_factory=dict)
    branch_split_detected: bool = False
    raw_context: str = field(repr=False, default="")
    snippet_file: str | None = None
