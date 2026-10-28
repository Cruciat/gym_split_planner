"""PDF di prova (issue #4). Verrà sostituito da ``GET /api/plans/{id}/pdf`` in M5."""

from fastapi import APIRouter
from fastapi.responses import Response

from gym_split_planner.services.pdf_test import build_test_pdf

router = APIRouter(tags=["sistema"])


@router.get(
    "/pdf/test",
    summary="PDF di prova",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}, "description": "PDF A4"}},
)
def get_test_pdf() -> Response:
    """Genera un PDF A4 di prova con tabella, simbolo SVG e numerazione delle pagine."""
    pdf = build_test_pdf()
    return Response(
        content=pdf.content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pdf.filename}"'},
    )
