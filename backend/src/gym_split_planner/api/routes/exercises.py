"""Creazione, modifica ed eliminazione degli esercizi (API, § 6.3; US-03, US-04, US-05)."""

from typing import Any

from fastapi import APIRouter, Request, Response
from sqlalchemy import Engine

from gym_split_planner.api.schemas.catalog import (
    ExerciseCreateIn,
    ExerciseDetailOut,
    ExerciseIn,
    ExerciseUsageOut,
)
from gym_split_planner.services.catalog import MuscleLinkData, TagLinkData
from gym_split_planner.services.exercises import (
    ExerciseInput,
    create_exercise,
    delete_exercise,
    get_exercise_usage,
    replace_exercise,
)

router = APIRouter(tags=["catalogo"])

_ERRORS: dict[int | str, dict[str, Any]] = {
    404: {"description": "Esercizio inesistente"},
    422: {
        "description": "Dati non validi (`validation-error`) o regola violata (`rule-violation`)"
    },
}


def _input(body: ExerciseIn) -> ExerciseInput:
    return ExerciseInput(
        name=body.name,
        primary_family_id=body.primary_family_id,
        secondary_family_id=body.secondary_family_id,
        family_rank=body.family_rank,
        equipment_id=body.equipment_id,
        equipment_detail=body.equipment_detail,
        kind=body.kind,
        stretch=body.stretch,
        stretch_note=body.stretch_note,
        confidence=body.confidence,
        notes=body.notes,
        is_active=body.is_active,
        muscles=tuple(MuscleLinkData(m.muscle_id, m.level, m.note) for m in body.muscles),
        tags=tuple(TagLinkData(t.tag_id, t.note) for t in body.tags),
        source_ids=tuple(body.source_ids),
    )


@router.post(
    "/exercises",
    response_model=ExerciseDetailOut,
    status_code=201,
    summary="Crea un esercizio",
    responses={422: _ERRORS[422]},
)
def post_exercise(
    request: Request, response: Response, body: ExerciseCreateIn
) -> ExerciseDetailOut:
    """Crea l'esercizio e restituisce il dettaglio, con ``Location``."""
    engine: Engine = request.app.state.engine
    detail = create_exercise(engine, _input(body), code=body.code)
    response.headers["Location"] = f"/api/exercises/{detail.id}"
    return ExerciseDetailOut.model_validate(detail)


@router.put(
    "/exercises/{exercise_id}",
    response_model=ExerciseDetailOut,
    summary="Sostituisce un esercizio",
    responses=_ERRORS,
)
def put_exercise(request: Request, exercise_id: int, body: ExerciseIn) -> ExerciseDetailOut:
    """Tutti i campi, compresi muscoli, etichette, fonti e ``is_active`` (disattivazione)."""
    engine: Engine = request.app.state.engine
    return ExerciseDetailOut.model_validate(replace_exercise(engine, exercise_id, _input(body)))


@router.get(
    "/exercises/{exercise_id}/usage",
    response_model=ExerciseUsageOut,
    summary="Dove è usato un esercizio",
    responses={404: _ERRORS[404]},
)
def read_exercise_usage(request: Request, exercise_id: int) -> ExerciseUsageOut:
    """Schede che lo usano, per scrivere la conferma di eliminazione."""
    engine: Engine = request.app.state.engine
    return ExerciseUsageOut.model_validate(get_exercise_usage(engine, exercise_id))


@router.delete(
    "/exercises/{exercise_id}",
    status_code=204,
    summary="Elimina un esercizio mai usato",
    responses={404: _ERRORS[404], 409: {"description": "Usato in una scheda (`in-use`)"}},
)
def remove_exercise(request: Request, exercise_id: int) -> Response:
    """Se l'esercizio è in una scheda: ``409 in-use`` con ``usage``; va disattivato."""
    engine: Engine = request.app.state.engine
    delete_exercise(engine, exercise_id)
    return Response(status_code=204)
