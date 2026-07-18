"""Writes inspection output to disk, MON-style folder shape:

    data/<domain>/
        clone/                raw fetched pages (cloner's own path-to-local
                               naming rules -- auto-index.html for extension-
                               less HTML routes, auto .js/.css suffixing)
        api_spec.json
        explorer.json
        explorer_visual.txt
        <domain>_full_report.<ext>

The clone/ path-mapping logic below is cloner's original filesystem.py
verbatim in spirit (same auto-index / auto-extension rules), just adapted
to run once at the end from context.pages instead of once per page mid-crawl.
"""

from __future__ import annotations

import os
from pathlib import Path

from mon.engine.context import InspectContext
from mon.exporters import get_exporter
from mon.models.result import InspectResult


def _unique_domain_folder(base_domain: str, output_dir: Path) -> tuple[str, Path]:
    """Cloner's get_unique_domain_folder: data/domain, data/domain_2, ..."""
    target = output_dir / base_domain
    if not target.exists():
        return base_domain, target
    counter = 2
    while True:
        candidate_name = f"{base_domain}_{counter}"
        candidate = output_dir / candidate_name
        if not candidate.exists():
            return candidate_name, candidate
        counter += 1


def path_to_local(clone_root: Path, path: str, content_type: str = "text/html") -> Path:
    """Cloner's filesystem.path_to_local, ported 1:1."""
    clean_path = path.split("?")[0]

    if clean_path == "/" or not clean_path.strip("/"):
        return clone_root / "index.html"

    parts = [p for p in clean_path.split("/") if p]
    last_part = parts[-1] if parts else ""
    has_extension = "." in last_part

    if "text/html" in content_type.lower() and not has_extension:
        local_file_path = clone_root.joinpath(*parts, "index.html")
    else:
        if "javascript" in content_type.lower() and not clean_path.endswith(".js"):
            clean_path += ".js"
        elif "css" in content_type.lower() and not clean_path.endswith(".css"):
            clean_path += ".css"
        local_file_path = clone_root / clean_path.lstrip("/")

    if local_file_path.name == ".html":
        local_file_path = local_file_path.parent / "index.html"

    return local_file_path


def write_output(context: InspectContext, result: InspectResult) -> Path | None:
    config = context.config
    if not config.save:
        return None

    domain_name, root = _unique_domain_folder(config.project_folder_name, config.output_dir)
    clone_dir = root / "clone"

    for page in context.pages.values():
        local_path = path_to_local(clone_dir, page.path, page.content_type)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(page.text, str):
            local_path.write_bytes(page.text.encode("utf-8"))
        else:
            local_path.write_bytes(page.text)

    root.mkdir(parents=True, exist_ok=True)

    if result.api_spec:
        _write_json(root / "api_spec.json", result.api_spec)

    if result.explorer:
        _write_json(root / "explorer.json", result.explorer)

    if result.explorer_visual:
        (root / "explorer_visual.txt").write_text(result.explorer_visual, encoding="utf-8")

    exporter = get_exporter(config.output_format)
    report_path = root / f"{domain_name}_full_report{exporter.extension}"
    report_path.write_text(exporter.export(result), encoding="utf-8")

    return root


def _write_json(path: Path, data: dict) -> None:
    import json
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
