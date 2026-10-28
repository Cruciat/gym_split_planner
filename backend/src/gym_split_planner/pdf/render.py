"""Motore comune: template Jinja2 → HTML → documento WeasyPrint."""

from functools import cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markupsafe import Markup
from weasyprint import HTML, Document

PACKAGE_DIR = Path(__file__).parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"
ICONS_DIR = PACKAGE_DIR / "icons"


@cache
def _environment() -> Environment:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.globals["icon"] = icon
    return environment


@cache
def icon(name: str) -> Markup:
    """SVG di un'icona Lucide, da inserire nel template (``{{ icon('warning') }}``)."""
    path = (ICONS_DIR / f"{name}.svg").resolve()
    if not path.is_relative_to(ICONS_DIR.resolve()) or not path.is_file():
        raise ValueError(f"Icona sconosciuta: {name}")
    return Markup(
        path.read_text(encoding="utf-8").strip()
    )  # file del pacchetto, non input dell'utente


def render_document(template: str, **context: Any) -> Document:
    """Impagina il template con il contesto e restituisce il documento (pagine incluse)."""
    html = _environment().get_template(template).render(**context)
    return HTML(string=html, base_url=str(TEMPLATES_DIR)).render()


def render_pdf(template: str, **context: Any) -> bytes:
    """Come ``render_document``, ma restituisce direttamente i byte del PDF."""
    pdf: bytes = render_document(template, **context).write_pdf()
    return pdf
