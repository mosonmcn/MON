"""Configuration Object Pattern.

Instead of every layer (Inspector, Dispatcher, analyzers...) accepting a long
list of positional parameters, they all accept a single immutable
:class:`InspectConfig` instance. This is built once, in :func:`mon.sdk.inspect`,
validated once, and then threaded through the entire pipeline unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mon.constants import (
    ACTION_ALL_DATA,
    ACTION_GROUPS,
    LEAF_ACTIONS,
    PROFILE_SETTINGS,
    VALID_OUTPUT_FORMATS,
    VALID_PROFILES,
)
from mon.exceptions import ConfigError


def _normalize_actions(action: str | list[str]) -> tuple[str, ...]:
    if isinstance(action, str):
        return (action,)
    if isinstance(action, (list, tuple)):
        if not action:
            raise ConfigError("'action' list must not be empty.")
        return tuple(action)
    raise ConfigError(f"'action' must be a str or list[str], got {type(action).__name__}.")


@dataclass(frozen=True, slots=True)
class InspectConfig:
    """Immutable settings for a single :func:`mon.inspect` call.

    Attributes mirror the public SDK signature exactly -- see
    :func:`mon.sdk.inspect` for the human-readable description of each field.
    """

    domain: str
    action: tuple[str, ...] = (ACTION_ALL_DATA,)
    profile: str = "balanced"
    file_type: str = "all"
    max_page: int | str = "all"
    allowed_files: str = "all"
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    project_name: str | None = None
    output_format: str = "python"
    response: bool | str = False
    timeout: int = 15
    save: bool = True
    overwrite: bool = False
    verify_ssl: bool = True
    unique_folder: bool = False

    def __post_init__(self) -> None:
        if not self.domain or not isinstance(self.domain, str):
            raise ConfigError("'domain' must be a non-empty string.")

        object.__setattr__(self, "action", _normalize_actions(self.action))
        for act in self.action:
            if act not in LEAF_ACTIONS and act not in ACTION_GROUPS:
                known = sorted(set(LEAF_ACTIONS) | set(ACTION_GROUPS))
                raise ConfigError(f"Unknown action '{act}'. Known actions: {known}")

        if self.profile not in VALID_PROFILES:
            raise ConfigError(f"'profile' must be one of {VALID_PROFILES}, got '{self.profile}'.")

        if self.output_format not in VALID_OUTPUT_FORMATS:
            raise ConfigError(
                f"'output_format' must be one of {VALID_OUTPUT_FORMATS}, got '{self.output_format}'."
            )

        if self.timeout <= 0:
            raise ConfigError("'timeout' must be a positive number of seconds.")

        if self.max_page != "all" and not isinstance(self.max_page, int):
            raise ConfigError("'max_page' must be an int or the literal string 'all'.")
        if isinstance(self.max_page, int) and self.max_page <= 0:
            raise ConfigError("'max_page' must be a positive integer when not 'all'.")

        object.__setattr__(self, "output_dir", Path(self.output_dir))

        object.__setattr__(self, "domain", self._clean_domain(self.domain))

    @staticmethod
    def _clean_domain(domain: str) -> str:
        cleaned = domain.strip()
        cleaned = cleaned.removeprefix("https://").removeprefix("http://")
        return cleaned.rstrip("/")

    @property
    def base_url(self) -> str:
        return f"https://{self.domain}"

    @property
    def resolved_max_page(self) -> int:
        if self.max_page == "all":
            return int(PROFILE_SETTINGS[self.profile]["max_page"])
        return int(self.max_page)

    @property
    def delay_seconds(self) -> float:
        return float(PROFILE_SETTINGS[self.profile]["delay_seconds"])

    @property
    def live_verify_enabled(self) -> bool:
        return bool(PROFILE_SETTINGS[self.profile]["live_verify"])

    @property
    def response_enabled(self) -> bool:
        return bool(self.response)

    @property
    def project_folder_name(self) -> str:
        return self.project_name or self.domain

    @property
    def output_path(self) -> Path:
        return self.output_dir / self.project_folder_name
