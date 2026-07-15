from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class FormField:
    """A single <input>/<select>/<textarea> discovered inside a <form>."""

    name: str
    type: str
    required: bool = False
    placeholder: str | None = None
    default_value: str | None = None


@dataclass(slots=True)
class Form:
    """A single <form> element discovered on a page."""

    page_url: str
    action: str
    method: str
    id: str | None = None
    css_class: str | None = None
    enctype: str | None = None
    fields: list[FormField] = field(default_factory=list)

    @property
    def field_names(self) -> list[str]:
        return [f.name for f in self.fields]
