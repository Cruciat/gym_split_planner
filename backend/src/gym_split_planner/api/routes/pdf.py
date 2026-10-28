"""PDF della scheda (US-30; API, § 6.10)."""

from typing import Annotated

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from gym_split_planner.services.plan_pdf import DEFAULT_WEEKS, plan_pdf

router = APIRouter(tags=["schede"])


@router.get(
    "/plans/{plan_id}/pdf",
    summary="PDF della scheda",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}, "description": "PDF A4"},
        404: {"description": "Scheda inesistente"},
    },
)
def get_plan_pdf(
    request: Request,
    plan_id: int,
    weeks: Annotated[int, Query(ge=1, le=8, description="Colonne per carichi e ripetizioni")] = (
        DEFAULT_WEEKS
    ),
) -> Response:
    """Una pagina per giorno e il riepilogo; il nome del file viene dalla scheda e dalla data."""
    pdf = plan_pdf(request.app.state.engine, plan_id, weeks)
    return Response(
        content=pdf.content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pdf.filename}"'},
    )
