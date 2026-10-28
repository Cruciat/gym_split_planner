"""Preferenze, giorni, slot e candidati di una scheda (API, § 6.6, § 6.7, § 6.8).

Tutte le modifiche richiedono ``If-Match`` e restituiscono la scheda completa.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Header, Query, Request, Response
from sqlalchemy import Engine

from gym_split_planner.api.revision import PRECONDITION_RESPONSES, expected_revision, set_etag
from gym_split_planner.api.schemas.plans import (
    CandidatesOut,
    DayIn,
    DayOrderIn,
    DayPatch,
    PlanOut,
    PlanSettingsOut,
    PreferencesIn,
    SlotIn,
    SlotOrderIn,
    SlotPatch,
)
from gym_split_planner.services.plan_candidates import slot_candidates
from gym_split_planner.services.plan_edit import (
    add_day,
    add_slot,
    delete_day,
    delete_slot,
    reorder_days,
    reorder_slots,
    update_day,
    update_slot,
)
from gym_split_planner.services.plan_settings import get_plan_settings, set_preferences
from gym_split_planner.services.plan_view import PlanViewData

router = APIRouter(tags=["schede"])

IfMatch = Annotated[str | None, Header(description='Revisione della scheda, es. `"17"`')]
_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"description": "Scheda o slot inesistente"}}


def _engine(request: Request) -> Engine:
    engine: Engine = request.app.state.engine
    return engine


def _plan(view: PlanViewData, response: Response) -> PlanOut:
    set_etag(response, view.revision)
    return PlanOut.model_validate(view)


# --- Preferenze ----------------------------------------------------------------------


@router.get(
    "/plans/{plan_id}/settings",
    response_model=PlanSettingsOut,
    summary="Preferenze e personalizzazioni",
    responses=_NOT_FOUND,
)
def read_plan_settings(request: Request, plan_id: int) -> PlanSettingsOut:
    """Per ogni muscolo ed etichetta: valore del catalogo, personalizzazione, effettivo."""
    return PlanSettingsOut.model_validate(get_plan_settings(_engine(request), plan_id))


@router.put(
    "/plans/{plan_id}/preferences",
    response_model=PlanOut,
    summary="Sostituisce le preferenze",
    responses=PRECONDITION_RESPONSES,
)
def put_plan_preferences(
    request: Request,
    response: Response,
    plan_id: int,
    body: PreferencesIn,
    if_match: IfMatch = None,
) -> PlanOut:
    """Normalizza e valida sui valori effettivi; non rigenera, aggiorna solo l'analisi."""
    revision = expected_revision(if_match)
    view = set_preferences(_engine(request), plan_id, body.model_dump(), revision)
    return _plan(view, response)


# --- Giorni --------------------------------------------------------------------------


@router.post(
    "/plans/{plan_id}/days",
    response_model=PlanOut,
    summary="Aggiunge un giorno",
    responses=PRECONDITION_RESPONSES,
)
def post_day(
    request: Request, response: Response, plan_id: int, body: DayIn, if_match: IfMatch = None
) -> PlanOut:
    revision = expected_revision(if_match)
    view = add_day(
        _engine(request), plan_id, body.name, body.times_per_week, body.position, revision
    )
    return _plan(view, response)


@router.put(
    "/plans/{plan_id}/days/order",
    response_model=PlanOut,
    summary="Riordina i giorni",
    responses=PRECONDITION_RESPONSES,
)
def put_day_order(
    request: Request,
    response: Response,
    plan_id: int,
    body: DayOrderIn,
    if_match: IfMatch = None,
) -> PlanOut:
    revision = expected_revision(if_match)
    return _plan(reorder_days(_engine(request), plan_id, body.day_ids, revision), response)


@router.patch(
    "/plans/{plan_id}/days/{day_id}",
    response_model=PlanOut,
    summary="Modifica un giorno",
    responses=PRECONDITION_RESPONSES,
)
def patch_day(
    request: Request,
    response: Response,
    plan_id: int,
    day_id: int,
    body: DayPatch,
    if_match: IfMatch = None,
) -> PlanOut:
    revision = expected_revision(if_match)
    changes = body.model_dump(exclude_unset=True)
    return _plan(update_day(_engine(request), plan_id, day_id, changes, revision), response)


@router.delete(
    "/plans/{plan_id}/days/{day_id}",
    response_model=PlanOut,
    summary="Elimina un giorno",
    responses=PRECONDITION_RESPONSES,
)
def remove_day(
    request: Request, response: Response, plan_id: int, day_id: int, if_match: IfMatch = None
) -> PlanOut:
    """Con i suoi slot; restituisce la scheda completa."""
    revision = expected_revision(if_match)
    return _plan(delete_day(_engine(request), plan_id, day_id, revision), response)


# --- Slot ----------------------------------------------------------------------------


@router.post(
    "/plans/{plan_id}/days/{day_id}/slots",
    response_model=PlanOut,
    summary="Aggiunge uno slot",
    responses=PRECONDITION_RESPONSES,
)
def post_slot(
    request: Request,
    response: Response,
    plan_id: int,
    day_id: int,
    body: SlotIn,
    if_match: IfMatch = None,
) -> PlanOut:
    revision = expected_revision(if_match)
    view = add_slot(_engine(request), plan_id, day_id, body.model_dump(), revision)
    return _plan(view, response)


@router.put(
    "/plans/{plan_id}/days/{day_id}/slots/order",
    response_model=PlanOut,
    summary="Riordina gli slot di un giorno",
    responses=PRECONDITION_RESPONSES,
)
def put_slot_order(
    request: Request,
    response: Response,
    plan_id: int,
    day_id: int,
    body: SlotOrderIn,
    if_match: IfMatch = None,
) -> PlanOut:
    revision = expected_revision(if_match)
    view = reorder_slots(_engine(request), plan_id, day_id, body.slot_ids, revision)
    return _plan(view, response)


@router.patch(
    "/plans/{plan_id}/slots/{slot_id}",
    response_model=PlanOut,
    summary="Modifica uno slot",
    responses=PRECONDITION_RESPONSES,
)
def patch_slot(
    request: Request,
    response: Response,
    plan_id: int,
    slot_id: int,
    body: SlotPatch,
    if_match: IfMatch = None,
) -> PlanOut:
    """Esercizio, variante della seconda seduta, famiglia, serie, ripetizioni, facoltativo,
    settimane alterne, lucchetto, nota: tutto o niente."""
    revision = expected_revision(if_match)
    changes = body.model_dump(exclude_unset=True)
    return _plan(update_slot(_engine(request), plan_id, slot_id, changes, revision), response)


@router.delete(
    "/plans/{plan_id}/slots/{slot_id}",
    response_model=PlanOut,
    summary="Elimina uno slot",
    responses=PRECONDITION_RESPONSES,
)
def remove_slot(
    request: Request, response: Response, plan_id: int, slot_id: int, if_match: IfMatch = None
) -> PlanOut:
    revision = expected_revision(if_match)
    return _plan(delete_slot(_engine(request), plan_id, slot_id, revision), response)


@router.get(
    "/plans/{plan_id}/slots/{slot_id}/candidates",
    response_model=CandidatesOut,
    summary="Candidati di uno slot",
    responses=_NOT_FOUND,
)
def read_slot_candidates(
    request: Request,
    plan_id: int,
    slot_id: int,
    session: Annotated[int, Query(ge=1, le=2, description="1 principale, 2 seconda seduta")] = 1,
) -> CandidatesOut:
    """Con punteggio, voci del punteggio, esclusioni ed effetto sul volume. Non modifica nulla."""
    return CandidatesOut.model_validate(
        slot_candidates(_engine(request), plan_id, slot_id, session)
    )
