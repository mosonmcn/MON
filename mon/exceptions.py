"""Exception hierarchy for the cloner/MON engine.

Every error raised anywhere in the ``mon`` package inherits from
:class:`MonError`, so callers can catch one base class if they don't care
about the exact failure mode. Structure copied from MON's original
exception design.
"""

from __future__ import annotations


class MonError(Exception):
    """Base class for every exception raised by this engine."""


class ConfigError(MonError):
    """Raised when :class:`~mon.config.InspectConfig` receives invalid input."""


class ResolverError(MonError):
    """Raised when the dependency resolver cannot build a valid pipeline."""


class RegistryError(MonError):
    """Raised when an action name has no analyzer registered against it."""


class AnalyzerError(MonError):
    """Wraps whatever an analyzer's own run() raised, so every failure the
    dispatcher reports has one consistent shape."""

    def __init__(self, analyzer_name: str, original: Exception) -> None:
        self.analyzer_name = analyzer_name
        self.original = original
        super().__init__(f"Analyzer '{analyzer_name}' failed: {original}")


class NetworkError(MonError):
    """Raised for unrecoverable network failures."""


class ExportError(MonError):
    """Raised when an exporter cannot produce output in the requested format."""
