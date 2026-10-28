"""Famiglie di movimento (API, § 6.3; US-06)."""

from typing import Any

from fastapi import APIRouter, Request, Response
from sqlalchemy import Engine

from gym_split_planner.api.schemas.catalog import (
    FamilyIn,
    FamilyOut,
    FamilyPatch,
    FamilyUsageOut,
)
from gym_split_planner.services.families import (
    FamilyInput,
    create_family,
    delete_family,
    get_family_usage,
    update_family,
)

router = APIRouter(tags=["catalogo"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"description": "Famiglia inesistente"}}


@router.post("/families", response_model=FamilyOut, status_code=201, summary="Crea una famiglia")
def post_family(request: Request, response: Response, body: FamilyIn) -> FamilyOut:
    """La famiglia nuova va in fondo all'elenco."""
    engine: Engine = request.app.state.engine
    family = create_family(
        engine,
        FamilyInput(body.name, body.description, body.muscle_group_id),
        code=body.code,
    )
    response.headers["Location"] = f"/api/families/{family.id}"
    return FamilyOut.model_validate(family)


@router.patch(
    "/families/{family_id}",
    response_model=FamilyOut,
    summary="Modifica una famiglia",
    responses=_NOT_FOUND,
)
def patch_family(request: Request, family_id: int, body: FamilyPatch) -> FamilyOut:
    engine: Engine = request.app.state.engine
    changes = body.model_dump(exclude_unset=True)
    return FamilyOut.model_validate(update_family(engine, family_id, changes))


@router.get(
    "/families/{family_id}/usage",
    response_model=FamilyUsageOut,
    summary="Chi usa una famiglia",
    responses=_NOT_FOUND,
)
def read_family_usage(request: Request, family_id: int) -> FamilyUsageOut:
    engine: Engine = request.app.state.engine
    return FamilyUsageOut.model_validate(get_family_usage(engine, family_id))


@router.delete(
    "/families/{family_id}",
    status_code=204,
    summary="Elimina una famiglia non usata",
    responses={**_NOT_FOUND, 409: {"description": "Famiglia in uso (`in-use`)"}},
)
def remove_family(request: Request, family_id: int) -> Response:
    """Rifiutata se ha esercizi principali, slot di split o di schede (C5)."""
    engine: Engine = request.app.state.engine
    delete_family(engine, family_id)
    return Response(status_code=204)
