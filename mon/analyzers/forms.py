from __future__ import annotations

from mon.analyzers.base import BaseAnalyzer
from mon.constants import ACTION_CRAWLER, ACTION_FORMS
from mon.engine.context import InspectContext
from mon.models.form import Form, FormField
from mon.parsers.html_parser import HTMLDocument


class FormsAnalyzer(BaseAnalyzer):
    """Extracts every <form> and its fields (name/type/required/placeholder/
    default value) from every crawled HTML page."""

    name = ACTION_FORMS
    description = "Extract forms and their input fields from crawled pages."
    priority = 20
    dependencies: tuple[str, ...] = (ACTION_CRAWLER,)

    def run(self, context: InspectContext) -> None:
        domain = context.config.domain
        for page in context.html_pages():
            doc = HTMLDocument(page.text, page.url, domain)
            for raw_form in doc.forms():
                context.forms.append(
                    Form(
                        page_url=page.url,
                        action=raw_form.action,
                        method=raw_form.method,
                        id=raw_form.id,
                        css_class=raw_form.css_class,
                        enctype=raw_form.enctype,
                        fields=[
                            FormField(
                                name=f.name, type=f.type, required=f.required,
                                placeholder=f.placeholder, default_value=f.default_value,
                            )
                            for f in raw_form.fields
                        ],
                    )
                )

    def summary(self, context: InspectContext) -> str | None:
        return f"forms {len(context.forms)}"
