"""Public SDK.

Per the spec: *"The framework exposes only one public function."* Everything
else in ``mon`` is an implementation detail callers should never need to
import directly.
"""

from __future__ import annotations

from pathlib import Path

from mon.config import InspectConfig
from mon.engine.inspector import Inspector
from mon.models.result import InspectResult


def inspect(
    domain: str,
    action: str | list[str] = "all_data",
    profile: str = "balanced",
    file_type: str = "all",
    max_page: int | str = "all",
    allowed_files: str = "all",
    output_dir: str | Path = "./output",
    project_name: str | None = None,
    output_format: str = "python",
    response: bool | str = False,
    timeout: int = 15,
    save: bool = True,
    overwrite: bool = False,
    verify_ssl: bool = True,
    unique_folder: bool = False,
) -> InspectResult:
    """Inspect a website and reconstruct its frontend/backend structure.

    Args:
        domain: Target domain, with or without a scheme (e.g. ``"example.com"``).
        action: One action name, or a list of them. Built-in leaf actions:
            crawler, html, javascript, forms, api, routes, assets, metadata,
            technology, server_info, relationships, explorer. Built-in
            composite actions: all_data, frontend, backend, api_spec,
            explorer_visual, cloning.
        profile: "fast" | "balanced" | "deep" -- controls crawl depth/breadth
            and whether live API verification runs.
        file_type: Reserved for future asset-type filtering.
        max_page: Max pages to crawl, or "all" to use the profile's default.
        allowed_files: Reserved for future crawl-scope filtering.
        output_dir: Base directory for saved output (only used if ``save=True``).
        project_name: Subfolder name under ``output_dir``; defaults to ``domain``.
        output_format: "python" | "json" | "markdown" | "html" | "yaml".
        response: Falsy for silent operation; truthy (e.g. ``"info"``) to log
            human-readable progress as the inspection runs.
        timeout: Per-request timeout in seconds.
        save: Whether to write the result to ``output_dir`` at all.
        overwrite: Whether an existing output file may be overwritten.
        verify_ssl: Whether to verify TLS certificates.
        unique_folder: If True, never merge into an existing output folder --
            allocate a fresh <name>_2, <name>_3, ... folder instead, matching
            a snapshot-per-run workflow rather than an accumulating one.

    Returns:
        An :class:`~mon.models.result.InspectResult`.
    """
    config = InspectConfig(
        domain=domain,
        action=action,
        profile=profile,
        file_type=file_type,
        max_page=max_page,
        allowed_files=allowed_files,
        output_dir=Path(output_dir),
        project_name=project_name,
        output_format=output_format,
        response=response,
        timeout=timeout,
        save=save,
        overwrite=overwrite,
        verify_ssl=verify_ssl,
        unique_folder=unique_folder,
    )

    result = Inspector(config).run()
    return result
