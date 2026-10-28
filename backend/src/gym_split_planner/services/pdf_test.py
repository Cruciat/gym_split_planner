"""PDF di prova (issue #4): verifica WeasyPrint nell'immagine prima di M5.

Verrà rimosso quando arriva il PDF vero della scheda (US-30).
"""

from dataclasses import dataclass
from datetime import date

from gym_split_planner import __version__
from gym_split_planner.pdf.render import render_pdf

TEMPLATE = "test.html"
WEEKS = 4


@dataclass(frozen=True)
class _Row:
    name: str
    sets: str
    rir: str
    rest: str
    sub: str = ""
    warning: bool = False
    note_ref: int = 0


_ROWS = (
    _Row("Chest press inclinata", "3 × 6-12", "0-2", "2-3′"),
    _Row("Chest press seduta", "3 × 6-12", "0-2", "2-3′"),
    _Row("Pec deck", "3 × 10-20", "0-2*", "90″"),
    _Row(
        "Estensione sopra la testa ai cavi",
        "3 × 10-15",
        "0-2*",
        "90″",
        sub="2ª seduta: estensione alla macchina",
        warning=True,
        note_ref=1,
    ),
    _Row("Pushdown con barra", "2 × 10-15", "0-2*", "90″"),
)


@dataclass(frozen=True)
class PdfFile:
    """PDF pronto da scaricare."""

    filename: str
    content: bytes


def build_test_pdf(today: date | None = None) -> PdfFile:
    """Genera il PDF di prova con la data indicata (oggi se assente)."""
    today = today or date.today()
    content = render_pdf(
        TEMPLATE,
        version=__version__,
        generated_on=today.strftime("%d/%m/%Y"),
        weeks=WEEKS,
        rows=_ROWS,
    )
    return PdfFile(filename=f"prova-pdf-{today.isoformat()}.pdf", content=content)
