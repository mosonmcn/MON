from __future__ import annotations

from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag

from mon.parsers.url_utils import normalize_path


@dataclass(slots=True)
class RawFormField:
    name: str
    type: str
    required: bool
    placeholder: str | None
    default_value: str | None


@dataclass(slots=True)
class RawForm:
    action: str
    method: str
    id: str | None
    css_class: str | None
    enctype: str | None
    fields: list[RawFormField] = field(default_factory=list)


@dataclass(slots=True)
class RawScript:
    src: str | None
    inline: bool
    content: str


class HTMLDocument:
    """Parses one HTML page once and exposes every extraction an analyzer
    might need. Analyzers should never call BeautifulSoup directly -- doing
    the parse once here and sharing the result avoids re-parsing the same
    markup in HtmlAnalyzer, JavascriptAnalyzer and FormsAnalyzer separately.
    """

    def __init__(self, html: str, page_url: str, domain: str) -> None:
        self.page_url = page_url
        self.domain = domain
        self.soup = BeautifulSoup(html, "html.parser")

    @property
    def title(self) -> str | None:
        if self.soup.title and self.soup.title.string:
            return self.soup.title.string.strip()
        return None

    def meta_description(self) -> str | None:
        tag = self.soup.find("meta", attrs={"name": "description"})
        if isinstance(tag, Tag):
            content = tag.get("content")
            return str(content).strip() if content else None
        return None

    def meta_generator(self) -> str | None:
        tag = self.soup.find("meta", attrs={"name": "generator"})
        if isinstance(tag, Tag):
            content = tag.get("content")
            return str(content).strip() if content else None
        return None

    def discovered_links(self) -> list[str]:
        """Same-domain paths worth adding to the crawl queue.

        Anchor/link tags use ``href``; script/img/iframe/source tags use
        ``src``. These are kept as two explicit passes (not one combined
        attribute filter) so a <script src="..."> is never missed because it
        happens not to also carry an href.
        """
        paths: list[str] = []

        for tag in self.soup.find_all(["a", "link"], href=True):
            resolved = normalize_path(str(tag.get("href", "")), self.page_url, self.domain)
            if resolved:
                paths.append(resolved)

        for tag in self.soup.find_all(["script", "img", "iframe", "source"], src=True):
            resolved = normalize_path(str(tag.get("src", "")), self.page_url, self.domain)
            if resolved:
                paths.append(resolved)

        seen: set[str] = set()
        unique: list[str] = []
        for p in paths:
            if p not in seen:
                seen.add(p)
                unique.append(p)
        return unique

    def scripts(self) -> list[RawScript]:
        results: list[RawScript] = []
        for tag in self.soup.find_all("script"):
            src = tag.get("src")
            if src:
                results.append(RawScript(src=str(src), inline=False, content=""))
            elif tag.string:
                results.append(RawScript(src=None, inline=True, content=str(tag.string)))
        return results

    def forms(self) -> list[RawForm]:
        results: list[RawForm] = []
        for form_tag in self.soup.find_all("form"):
            fields: list[RawFormField] = []
            for input_tag in form_tag.find_all(["input", "select", "textarea"]):
                name = input_tag.get("name")
                if not name:
                    continue
                fields.append(
                    RawFormField(
                        name=str(name),
                        type=str(input_tag.get("type", input_tag.name)),
                        required=input_tag.has_attr("required"),
                        placeholder=(str(input_tag.get("placeholder")) if input_tag.get("placeholder") else None),
                        default_value=(str(input_tag.get("value")) if input_tag.get("value") else None),
                    )
                )
            results.append(
                RawForm(
                    action=str(form_tag.get("action", "")),
                    method=str(form_tag.get("method", "GET")).upper(),
                    id=(str(form_tag.get("id")) if form_tag.get("id") else None),
                    css_class=(" ".join(form_tag.get("class", [])) or None),
                    enctype=(str(form_tag.get("enctype")) if form_tag.get("enctype") else None),
                    fields=fields,
                )
            )
        return results

    def images(self) -> list[str]:
        return [str(tag.get("src")) for tag in self.soup.find_all("img", src=True)]

    def stylesheets(self) -> list[str]:
        return [
            str(tag.get("href"))
            for tag in self.soup.find_all("link", rel="stylesheet")
            if tag.get("href")
        ]
