"""Etichette (API, § 6.3; US-08, ADR 0014)."""

from typing import Any

from fastapi import APIRouter, Request, Response
from sqlalchemy import Engine

from gym_split_planner.api.schemas.catalog import (
    TagAssignIn,
    TagIn,
    TagOut,
    TagPatch,
    TagUnassignIn,
    TagUsageOut,
)
from gym_split_planner.services.tags import (
    TagInput,
    assign_tag,
    create_tag,
    delete_tag,
    get_tag_usage,
    unassign_tag,
    update_tag,
)

router = APIRouter(tags=["catalogo"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"description": "Etichetta inesistente"}}


@router.post("/tags", response_model=TagOut, status_code=201, summary="Crea un'etichetta")
def post_tag(request: Request, response: Response, body: TagIn) -> TagOut:
    engine: Engine = request.app.state.engine
    tag = create_tag(
        engine,
        TagInput(
            name=body.name,
            description=body.description,
            symbol=body.symbol,
            color=body.color,
            effect=body.effect,
            points=body.points,
            show_badge=body.show_badge,
        ),
        code=body.code,
    )
    response.headers["Location"] = f"/api/tags/{tag.id}"
    return TagOut.model_validate(tag)


@router.patch(
    "/tags/{tag_id}", response_model=TagOut, summary="Modifica un'etichetta", responses=_NOT_FOUND
)
def patch_tag(request: Request, tag_id: int, body: TagPatch) -> TagOut:
    """Effetto e punti valgono subito per le schede che non li personalizzano."""
    engine: Engine = request.app.state.engine
    changes = body.model_dump(exclude_unset=True)
    return TagOut.model_validate(update_tag(engine, tag_id, changes))


@router.get(
    "/tags/{tag_id}/usage",
    response_model=TagUsageOut,
    summary="Chi usa un'etichetta",
    responses=_NOT_FOUND,
)
def read_tag_usage(request: Request, tag_id: int) -> TagUsageOut:
    engine: Engine = request.app.state.engine
    return TagUsageOut.model_validate(get_tag_usage(engine, tag_id))


@router.delete(
    "/tags/{tag_id}", status_code=204, summary="Elimina un'etichetta", responses=_NOT_FOUND
)
def remove_tag(request: Request, tag_id: int) -> Response:
    """Toglie anche assegnazioni e personalizzazioni delle schede; il client chiede
    conferma dopo aver letto gli utilizzi (US-08 CA3)."""
    engine: Engine = request.app.state.engine
    delete_tag(engine, tag_id)
    return Response(status_code=204)


@router.post(
    "/tags/{tag_id}/assign",
    response_model=TagUsageOut,
    summary="Assegna un'etichetta a più esercizi",
    responses=_NOT_FOUND,
)
def post_tag_assign(request: Request, tag_id: int, body: TagAssignIn) -> TagUsageOut:
    engine: Engine = request.app.state.engine
    usage = assign_tag(
        engine, tag_id, body.exercise_ids, body.note, set_note="note" in body.model_fields_set
    )
    return TagUsageOut.model_validate(usage)


@router.post(
    "/tags/{tag_id}/unassign",
    response_model=TagUsageOut,
    summary="Toglie un'etichetta da più esercizi",
    responses=_NOT_FOUND,
)
def post_tag_unassign(request: Request, tag_id: int, body: TagUnassignIn) -> TagUsageOut:
    engine: Engine = request.app.state.engine
    return TagUsageOut.model_validate(unassign_tag(engine, tag_id, body.exercise_ids))
