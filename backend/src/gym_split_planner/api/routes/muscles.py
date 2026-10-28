"""Muscoli: priorità e fascia del catalogo (API, § 6.3; US-07)."""

from fastapi import APIRouter, Request
from sqlalchemy import Engine

from gym_split_planner.api.schemas.catalog import MuscleOut, MusclePatch
from gym_split_planner.services.muscles import update_muscle

router = APIRouter(tags=["catalogo"])


@router.patch(
    "/muscles/{muscle_id}",
    response_model=MuscleOut,
    summary="Modifica un muscolo",
    responses={
        404: {"description": "Muscolo inesistente"},
        409: {"description": "La fascia renderebbe invalida una scheda (`invalid-band`)"},
    },
)
def patch_muscle(request: Request, muscle_id: int, body: MusclePatch) -> MuscleOut:
    """Nomi, priorità, fascia e note. Vale subito per le schede che non lo personalizzano."""
    engine: Engine = request.app.state.engine
    changes = body.model_dump(exclude_unset=True)
    return MuscleOut.model_validate(update_muscle(engine, muscle_id, changes))
