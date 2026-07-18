"""Importing this package registers every built-in analyzer.

Adding a new analyzer is purely additive: write the class in its own file,
import it here, call register_action(). Nothing in the engine layer needs
to change.
"""

from mon.analyzers.api import ApiAnalyzer
from mon.analyzers.assets import AssetsAnalyzer
from mon.analyzers.crawler import CrawlerAnalyzer
from mon.analyzers.explorer import ExplorerAnalyzer
from mon.analyzers.html import HtmlAnalyzer
from mon.analyzers.javascript import JavascriptAnalyzer
from mon.analyzers.routes import RoutesAnalyzer
from mon.engine.registry import register_action

register_action(CrawlerAnalyzer.name, CrawlerAnalyzer)
register_action(HtmlAnalyzer.name, HtmlAnalyzer)
register_action(JavascriptAnalyzer.name, JavascriptAnalyzer)
register_action(ApiAnalyzer.name, ApiAnalyzer)
register_action(RoutesAnalyzer.name, RoutesAnalyzer)
register_action(AssetsAnalyzer.name, AssetsAnalyzer)
register_action(ExplorerAnalyzer.name, ExplorerAnalyzer)

__all__ = [
    "ApiAnalyzer", "AssetsAnalyzer", "CrawlerAnalyzer", "ExplorerAnalyzer",
    "HtmlAnalyzer", "JavascriptAnalyzer", "RoutesAnalyzer",
]
