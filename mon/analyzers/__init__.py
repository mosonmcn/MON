"""Importing this package registers every built-in analyzer.

Adding a new analyzer is a two-step, purely additive process:
  1. Write the analyzer class in its own file under mon/analyzers/.
  2. Import it here and call register_action() -- nothing else in the
     engine (Inspector, Resolver, Dispatcher) needs to change.
"""

from mon.analyzers.api import ApiAnalyzer
from mon.analyzers.assets import AssetsAnalyzer
from mon.analyzers.crawler import CrawlerAnalyzer
from mon.analyzers.explorer import ExplorerAnalyzer
from mon.analyzers.forms import FormsAnalyzer
from mon.analyzers.html import HtmlAnalyzer
from mon.analyzers.javascript import JavascriptAnalyzer
from mon.analyzers.metadata import MetadataAnalyzer
from mon.analyzers.relationships import RelationshipsAnalyzer
from mon.analyzers.routes import RoutesAnalyzer
from mon.analyzers.server import ServerAnalyzer
from mon.analyzers.technology import TechnologyAnalyzer
from mon.engine.registry import register_action

register_action(CrawlerAnalyzer.name, CrawlerAnalyzer)
register_action(HtmlAnalyzer.name, HtmlAnalyzer)
register_action(JavascriptAnalyzer.name, JavascriptAnalyzer)
register_action(FormsAnalyzer.name, FormsAnalyzer)
register_action(ApiAnalyzer.name, ApiAnalyzer)
register_action(RoutesAnalyzer.name, RoutesAnalyzer)
register_action(AssetsAnalyzer.name, AssetsAnalyzer)
register_action(MetadataAnalyzer.name, MetadataAnalyzer)
register_action(TechnologyAnalyzer.name, TechnologyAnalyzer)
register_action(ServerAnalyzer.name, ServerAnalyzer)
register_action(RelationshipsAnalyzer.name, RelationshipsAnalyzer)
register_action(ExplorerAnalyzer.name, ExplorerAnalyzer)

__all__ = [
    "ApiAnalyzer",
    "AssetsAnalyzer",
    "CrawlerAnalyzer",
    "ExplorerAnalyzer",
    "FormsAnalyzer",
    "HtmlAnalyzer",
    "JavascriptAnalyzer",
    "MetadataAnalyzer",
    "RelationshipsAnalyzer",
    "RoutesAnalyzer",
    "ServerAnalyzer",
    "TechnologyAnalyzer",
]
