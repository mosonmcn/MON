"""Exception hierarchy for the MON engine.

All errors raised anywhere inside the mon package inherit from :class:`MonError`
so callers can catch a single base class if they don't care about the exact
failure mode.
"""

from __future__ import annotations


class MonError(Exception):
    """Base class for every exception raised by MON."""


class ConfigError(MonError):
    """Raised when :class:`~mon.config.InspectConfig` receives invalid input."""


class ResolverError(MonError):
    """Raised when the dependency resolver cannot build a valid pipeline.

    Typical causes: an unknown action name, or a circular dependency between
    two or more analyzers.
    """


class RegistryError(MonError):
    """Raised when an action name has no analyzer registered against it."""


class AnalyzerError(MonError):
    """Raised when an analyzer fails during ``before_run``/``run``/``after_run``.

    The dispatcher wraps the analyzer's own exception in this type so the
    inspection pipeline always reports failures using one consistent shape,
    regardless of what the individual analyzer raised internally.
    """

    def __init__(self, analyzer_name: str, original: Exception) -> None:
        self.analyzer_name = analyzer_name
        self.original = original
        super().__init__(f"Analyzer '{analyzer_name}' failed: {original}")


class NetworkError(MonError):
    """Raised for unrecoverable network failures (after retries are exhausted)."""


class ExportError(MonError):
    """Raised when an exporter cannot produce output in the requested format."""
