from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any

from mon.models.endpoint import Endpoint
from mon.models.form import Form
from mon.models.relationship import RelationshipChain
from mon.models.route import Route
from mon.models.technology import ServerInfo, Technology


def _to_plain(value: Any) -> Any:
    """Recursively convert dataclasses (and containers of them) into plain
    dict/list/scalar structures, suitable for JSON/YAML export."""
    if is_dataclass(value) and not isinstance(value, type):
        return {k: _to_plain(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_plain(v) for v in value]
    return value


@dataclass(slots=True)
class InspectResult:
    """The object returned by :func:`mon.inspect`.

    This is intentionally not a plain dictionary -- callers get attribute
    access (``result.apis``, ``result.forms``, ...) with real types behind
    each attribute, while :meth:`to_dict` remains available for anyone who
    wants the raw structure (used by every exporter).
    """

    domain: str
    actions_run: tuple[str, ...]

    apis: list[Endpoint] = field(default_factory=list)
    forms: list[Form] = field(default_factory=list)
    routes: list[Route] = field(default_factory=list)
    server: ServerInfo | None = None
    technology: list[Technology] = field(default_factory=list)
    explorer: dict = field(default_factory=dict)
    explorer_visual: str = ""
    api_spec: dict = field(default_factory=dict)
    relationships: list[RelationshipChain] = field(default_factory=list)

    pages_crawled: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "actions_run": list(self.actions_run),
            "apis": [_to_plain(a) for a in self.apis],
            "forms": [_to_plain(f) for f in self.forms],
            "routes": [_to_plain(r) for r in self.routes],
            "server": _to_plain(self.server) if self.server else None,
            "technology": [_to_plain(t) for t in self.technology],
            "explorer": self.explorer,
            "explorer_visual": self.explorer_visual,
            "api_spec": self.api_spec,
            "relationships": [_to_plain(r) for r in self.relationships],
            "pages_crawled": self.pages_crawled,
            "warnings": self.warnings,
        }
