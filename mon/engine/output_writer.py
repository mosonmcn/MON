"""Writes inspection output to disk as a structured, domain-scoped folder:

    output/<safe-name>/
        clone/               raw fetched pages, mirroring the site's own
                              path structure. HTML routes become
                              <route>/index.html (a real folder per route,
                              like a browser/file-manager would expect --
                              never a flat '<route>.html' file that would
                              collide with a same-named subroute folder).
        data/
            explorer.json           flat, merge-safe {path: {type,title}}
            explorer_visual.txt     folder-first ASCII tree, rebuilt from
                                     the MERGED route data every run
            api_spec.json
            <name>_full_report.<ext>

This intentionally runs from *inside* :class:`~mon.engine.inspector.Inspector`
(not from the SDK after the fact), because writing ``clone/`` needs
``context.pages`` -- raw page text that deliberately never makes it into the
lean, JSON-friendly :class:`~mon.models.result.InspectResult`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from mon.analyzers.route_tree import build_tree, render_root
from mon.engine.context import InspectContext
from mon.exporters import get_exporter
from mon.models.result import InspectResult
from mon.models.route import Route

_UNSAFE_CHARS = re.compile(r"[^a-zA-Z0-9._-]+")


def safe_folder_name(target: str) -> str:
    """Turn a domain, URL, git URL, or local path into a filesystem-safe
    folder name, e.g. 'https://github.com/a/b' -> 'github.com_a_b'."""
    cleaned = target.strip()
    cleaned = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", "", cleaned)  # strip any scheme
    cleaned = cleaned.rstrip("/")
    cleaned = _UNSAFE_CHARS.sub("_", cleaned)
    return cleaned or "target"


def _resolve_output_root(output_dir: Path, folder_name: str, unique_folder: bool) -> Path:
    """Return the output root folder for this run.

    Default (unique_folder=False): reuse output_dir/<folder_name>, merging
    new data into whatever a previous run already wrote there.

    unique_folder=True: never merge -- if output_dir/<folder_name> already
    exists, allocate output_dir/<folder_name>_2, _3, etc., matching a
    fresh-snapshot-per-run workflow instead of an accumulating one.
    """
    base = output_dir / folder_name
    if not unique_folder or not base.exists():
        return base

    counter = 2
    while (output_dir / f"{folder_name}_{counter}").exists():
        counter += 1
    return output_dir / f"{folder_name}_{counter}"


def _page_to_local_path(clone_root: Path, page_path: str, content_type: str) -> Path:
    """Map a crawled page's route to a file under clone/.

    HTML routes become a real folder containing index.html (e.g. '/register'
    -> 'register/index.html'), so a subroute like '/register/terms' can
    always nest safely as 'register/terms/index.html' without ever
    colliding with a flat 'register.html' file for the parent route.
    Anything with a real file extension (.js, .css, .png, ...) is written
    as-is, preserving the site's own directory structure.
    """
    trimmed = page_path.strip("/")

    if not trimmed:
        return clone_root / "index.html"

    last_segment = trimmed.rsplit("/", 1)[-1]
    if "." in last_segment:
        return clone_root / trimmed

    if "text/html" in content_type:
        return clone_root / trimmed / "index.html"

    return clone_root / trimmed


def _load_existing_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError):
        return {}


def _write_json_merged(path: Path, new_data: dict, overwrite: bool) -> dict:
    """Write a dict as JSON, merging with whatever is already on disk unless
    overwrite=True. Returns the final (merged) data that was written, so
    callers can derive further output (like the explorer visual tree) from
    the same merged view rather than the current run's data alone."""
    path.parent.mkdir(parents=True, exist_ok=True)

    final_data = dict(new_data)
    if not overwrite:
        existing = _load_existing_json(path)
        merged = dict(existing)
        merged.update(new_data)
        final_data = merged

    path.write_text(json.dumps(final_data, indent=2, ensure_ascii=False), encoding="utf-8")
    return final_data


def write_output(context: InspectContext, result: InspectResult) -> Path | None:
    """Write the full domain-scoped output folder. Returns the folder path,
    or None if ``config.save`` is False."""
    config = context.config
    if not config.save:
        return None

    folder_name = safe_folder_name(config.project_folder_name)
    root = _resolve_output_root(config.output_dir, folder_name, config.unique_folder)
    clone_dir = root / "clone"
    data_dir = root / "data"

    for page in context.pages.values():
        local_path = _page_to_local_path(clone_dir, page.path, page.content_type)
        if local_path.exists() and not config.overwrite:
            continue
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(page.text, encoding="utf-8")

    if result.api_spec:
        _write_json_merged(data_dir / "api_spec.json", result.api_spec, config.overwrite)

    # explorer.json: flat, merge-safe {path: {type, title}} -- then the
    # visual .txt tree is rebuilt from this MERGED view, not just the
    # current run's routes, so a partial re-crawl never shrinks the tree.
    current_routes_flat = {
        route.path: {"type": route.type, "title": route.title} for route in context.routes
    }
    merged_routes_flat = _write_json_merged(data_dir / "explorer.json", current_routes_flat, config.overwrite)

    merged_route_objects = [
        Route(path=path, file=path.rsplit("/", 1)[-1] or "index.html",
              type=meta.get("type", "asset"), title=meta.get("title"))
        for path, meta in merged_routes_flat.items()
    ]
    tree = build_tree(merged_route_objects)
    (data_dir / "explorer_visual.txt").write_text("\n".join(render_root(config.domain, tree)), encoding="utf-8")

    exporter = get_exporter(config.output_format)
    report_path = data_dir / f"{folder_name}_full_report{exporter.extension}"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(exporter.export(result), encoding="utf-8")

    return root
