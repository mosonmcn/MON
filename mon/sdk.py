"""Public SDK -- the framework exposes one public function."""

from __future__ import annotations

from pathlib import Path

from mon.config import InspectConfig
from mon.engine.inspector import Inspector
from mon.models.result import InspectResult


def inspect(
    domain: str,
    action: str | list[str] = "all_data",
    profile: str = "balanced",
    max_page: int | str = "all",
    output_dir: str | Path = "./data",
    project_name: str | None = None,
    output_format: str = "json",
    response: bool = True,
    timeout: int = 10,
    save: bool = True,
    verify_live_apis: bool = True,
) -> InspectResult:
    """Inspect a website and reconstruct its frontend/backend structure,
    using cloner's original fetch logic for every network call.

    Args:
        domain: Target domain, with or without a scheme.
        action: One action name or list of them. Leaf actions: crawler,
            html, javascript, api, routes, assets, explorer. Composite:
            all_data, api_spec, explorer_visual, cloning.
        profile: "fast" | "balanced" | "deep".
        max_page: Max pages to crawl, or "all" to use the profile's default.
        output_dir: Base directory for saved output.
        project_name: Subfolder name under output_dir; defaults to domain.
        output_format: "json" | "markdown".
        response: Whether to print live progress (cloner-style log lines).
        timeout: Per-request timeout in seconds.
        save: Whether to write output to disk at all.
        verify_live_apis: Whether to live-verify reconstructed endpoints
            against the real server (cloner's api_verifier.py logic).
    """
    config = InspectConfig(
        domain=domain,
        action=action,
        profile=profile,
        max_page=max_page,
        output_dir=Path(output_dir),
        project_name=project_name,
        output_format=output_format,
        response=response,
        timeout=timeout,
        save=save,
        verify_live_apis=verify_live_apis,
    )
    return Inspector(config).run()
