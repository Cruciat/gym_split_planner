"""Split predefiniti e schede (API, § 6.4, § 6.5; US-10, US-12, US-13, US-19)."""

from typing import Annotated, Any

from fastapi import APIRouter, Header, Request, Response
from sqlalchemy import Engine

from gym_split_planner.api.revision import PRECONDITION_RESPONSES, expected_revision, set_etag
from gym_split_planner.api.schemas.plans import (
    PlanCreateIn,
    PlanOut,
    PlanRenameIn,
    PlanSummaryOut,
    SplitOut,
)
from gym_split_planner.services.plan_view import PlanViewData
from gym_split_planner.services.plans import (
    activate_plan,
    create_plan,
    delete_plan,
    duplicate_plan,
    get_plan,
    list_plans,
    list_splits,
    rename_plan,
)

router = APIRouter(tags=["schede"])

IfMatch = Annotated[str | None, Header(description='Revisione della scheda, es. `"17"`')]
_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"description": "Scheda inesistente"}}


def _engine(request: Request) -> Engine:
    engine: Engine = request.app.state.engine
    return engine


def _plan(view: PlanViewData, response: Response) -> PlanOut:
    set_etag(response, view.revision)
    return PlanOut.model_validate(view)


@router.get("/splits", response_model=list[SplitOut], summary="Split predefiniti")
def read_splits(request: Request) -> list[SplitOut]:
    """Preset con giorni e slot, per la procedura guidata (US-10 CA1)."""
    return [SplitOut.model_validate(s) for s in list_splits(_engine(request))]


@router.get("/plans", response_model=list[PlanSummaryOut], summary="Elenco delle schede")
def read_plans(request: Request) -> list[PlanSummaryOut]:
    """Dalla modificata più di recente (US-19 CA1)."""
    return [PlanSummaryOut.model_validate(p) for p in list_plans(_engine(request))]


@router.post(
    "/plans",
    response_model=PlanOut,
    status_code=201,
    summary="Crea una scheda",
    responses={422: {"description": "Dati non validi o preferenze non valide"}},
)
def post_plan(request: Request, response: Response, body: PlanCreateIn) -> PlanOut:
    """Da uno split (copiato e generato, US-12) o vuota; restituisce la scheda completa."""
    preferences = body.preferences.model_dump() if body.preferences else None
    view = create_plan(_engine(request), body.split_id, body.name, preferences)
    response.headers["Location"] = f"/api/plans/{view.id}"
    return _plan(view, response)


@router.get(
    "/plans/{plan_id}", response_model=PlanOut, summary="Scheda completa", responses=_NOT_FOUND
)
def read_plan(request: Request, response: Response, plan_id: int) -> PlanOut:
    """Giorni, slot e analisi: volumi, sedute, avvisi (§ 7)."""
    return _plan(get_plan(_engine(request), plan_id), response)


@router.patch(
    "/plans/{plan_id}",
    response_model=PlanOut,
    summary="Rinomina una scheda",
    responses=PRECONDITION_RESPONSES,
)
def patch_plan(
    request: Request,
    response: Response,
    plan_id: int,
    body: PlanRenameIn,
    if_match: IfMatch = None,
) -> PlanOut:
    revision = expected_revision(if_match)
    return _plan(rename_plan(_engine(request), plan_id, body.name, revision), response)


@router.delete(
    "/plans/{plan_id}", status_code=204, summary="Elimina una scheda", responses=_NOT_FOUND
)
def remove_plan(request: Request, plan_id: int) -> Response:
    """Con giorni e slot. Non richiede ``If-Match``: la conferma è dell'interfaccia."""
    delete_plan(_engine(request), plan_id)
    return Response(status_code=204)


@router.post(
    "/plans/{plan_id}/duplicate",
    response_model=PlanOut,
    status_code=201,
    summary="Duplica una scheda",
    responses=_NOT_FOUND,
)
def post_plan_duplicate(request: Request, response: Response, plan_id: int) -> PlanOut:
    """Copia completa con nome "… (copia)", non attiva."""
    view = duplicate_plan(_engine(request), plan_id)
    response.headers["Location"] = f"/api/plans/{view.id}"
    return _plan(view, response)


@router.post(
    "/plans/{plan_id}/activate",
    response_model=PlanOut,
    summary="Rende attiva una scheda",
    responses=_NOT_FOUND,
)
def post_plan_activate(request: Request, response: Response, plan_id: int) -> PlanOut:
    """L'unica attiva; non cambia la revisione e non richiede ``If-Match``."""
    return _plan(activate_plan(_engine(request), plan_id), response)
