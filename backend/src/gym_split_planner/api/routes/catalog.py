"""Catalogo in lettura: ``GET /api/catalog`` e ``GET /api/exercises/{id}`` (API, § 6.2)."""

import hashlib

from fastapi import APIRouter, Header, Request, Response
from sqlalchemy import Engine

from gym_split_planner.api.errors import ApiProblem
from gym_split_planner.api.schemas.catalog import CatalogOut, ExerciseDetailOut
from gym_split_planner.services.catalog import get_catalog, get_exercise_detail

router = APIRouter(tags=["catalogo"])

JSON = "application/json"


@router.get(
    "/catalog",
    response_model=CatalogOut,
    summary="Tutto il catalogo",
    responses={304: {"description": "Catalogo invariato rispetto all'ETag inviato"}},
)
def read_catalog(
    request: Request,
    if_none_match: str | None = Header(default=None),
) -> Response:
    """Muscoli, famiglie, etichette, esercizi e il resto del catalogo in una risposta.

    L'``ETag`` è calcolato sul contenuto: con ``If-None-Match`` uguale la risposta è
    ``304`` senza corpo. ``Cache-Control: no-cache`` fa sì che il browser chieda
    sempre conferma al server, così una modifica al catalogo si vede subito.
    """
    engine: Engine = request.app.state.engine
    body = CatalogOut.model_validate(get_catalog(engine)).model_dump_json().encode()
    etag = f'"{hashlib.sha256(body).hexdigest()[:32]}"'
    headers = {"ETag": etag, "Cache-Control": "no-cache"}
    if if_none_match is not None and _etag_matches(if_none_match, etag):
        return Response(status_code=304, headers=headers)
    return Response(content=body, media_type=JSON, headers=headers)


@router.get(
    "/exercises/{exercise_id}",
    response_model=ExerciseDetailOut,
    summary="Dettaglio di un esercizio",
    responses={404: {"description": "Esercizio inesistente"}},
)
def read_exercise(request: Request, exercise_id: int) -> ExerciseDetailOut:
    """Tutti i campi, muscoli con note, etichette con note, fonti e varianti."""
    engine: Engine = request.app.state.engine
    detail = get_exercise_detail(engine, exercise_id)
    if detail is None:
        raise ApiProblem(
            404, "not-found", "Esercizio non trovato", f"Non esiste l'esercizio {exercise_id}."
        )
    return ExerciseDetailOut.model_validate(detail)


def _etag_matches(header: str, etag: str) -> bool:
    """Confronto debole (RFC 9110, § 13.1.2): ``*`` o uno degli ETag dell'elenco."""
    if header.strip() == "*":
        return True
    candidates = {value.strip().removeprefix("W/") for value in header.split(",")}
    return etag in candidates
