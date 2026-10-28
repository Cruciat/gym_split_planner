"""Fonti della ricerca (API, § 6.3), per la form dell'esercizio."""

from typing import Any

from fastapi import APIRouter, Request, Response
from sqlalchemy import Engine

from gym_split_planner.api.schemas.catalog import SourceIn, SourceOut, SourcePatch
from gym_split_planner.services.sources import (
    SourceInput,
    create_source,
    delete_source,
    update_source,
)

router = APIRouter(tags=["catalogo"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"description": "Fonte inesistente"}}


@router.post("/sources", response_model=SourceOut, status_code=201, summary="Crea una fonte")
def post_source(request: Request, response: Response, body: SourceIn) -> SourceOut:
    """Il codice è il successivo della serie ``src-NN``."""
    engine: Engine = request.app.state.engine
    source = create_source(engine, SourceInput(**body.model_dump()))
    response.headers["Location"] = f"/api/sources/{source.id}"
    return SourceOut.model_validate(source)


@router.patch(
    "/sources/{source_id}",
    response_model=SourceOut,
    summary="Modifica una fonte",
    responses=_NOT_FOUND,
)
def patch_source(request: Request, source_id: int, body: SourcePatch) -> SourceOut:
    """Cambiano solo i campi inviati; ``null`` svuota i campi facoltativi."""
    engine: Engine = request.app.state.engine
    changes = body.model_dump(exclude_unset=True)
    return SourceOut.model_validate(update_source(engine, source_id, changes))


@router.delete(
    "/sources/{source_id}", status_code=204, summary="Elimina una fonte", responses=_NOT_FOUND
)
def remove_source(request: Request, source_id: int) -> Response:
    """Toglie anche i collegamenti agli esercizi che la citano."""
    engine: Engine = request.app.state.engine
    delete_source(engine, source_id)
    return Response(status_code=204)
