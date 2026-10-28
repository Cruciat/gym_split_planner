"""PDF di prova (issue #4)."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from gym_split_planner.pdf.render import icon, render_document
from gym_split_planner.services.pdf_test import _ROWS, TEMPLATE, WEEKS, build_test_pdf


def test_endpoint_returns_a4_pdf_attachment(client: TestClient) -> None:
    response = client.get("/api/pdf/test")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith('attachment; filename="prova-pdf-')
    assert response.content.startswith(b"%PDF-")


def test_test_document_is_one_a4_page() -> None:
    document = render_document(
        TEMPLATE, version="0.0.0", generated_on="28/10/2026", weeks=WEEKS, rows=_ROWS
    )

    assert len(document.pages) == 1
    page = document.pages[0]
    # A4 in punti CSS (1 mm = 96/25,4 px): 210 × 297 mm.
    assert round(page.width * 25.4 / 96) == 210
    assert round(page.height * 25.4 / 96) == 297


def test_filename_uses_the_date() -> None:
    pdf = build_test_pdf(date(2026, 10, 28))

    assert pdf.filename == "prova-pdf-2026-10-28.pdf"


def test_icon_inlines_svg() -> None:
    assert icon("warning").startswith("<svg")


@pytest.mark.parametrize("name", ["non-esiste", "../templates/test"])
def test_unknown_or_outside_icon_is_rejected(name: str) -> None:
    with pytest.raises(ValueError, match="Icona sconosciuta"):
        icon(name)
