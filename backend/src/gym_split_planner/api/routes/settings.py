"""Impostazioni globali (API, § 6.1; US-20)."""

from fastapi import APIRouter, Request
from sqlalchemy import Engine

from gym_split_planner.api.schemas.settings import SettingsIO
from gym_split_planner.services.settings import (
    get_default_settings,
    get_settings,
    replace_settings,
)

router = APIRouter(tags=["sistema"])


def _engine(request: Request) -> Engine:
    engine: Engine = request.app.state.engine
    return engine


@router.get("/settings", response_model=SettingsIO, summary="Impostazioni globali")
def read_settings(request: Request) -> SettingsIO:
    """Pesi dei livelli, tetto per seduta, pesi del punteggio, durata, riscaldamento, RIR."""
    return SettingsIO.model_validate(get_settings(_engine(request)))


@router.get("/settings/defaults", response_model=SettingsIO, summary="Impostazioni predefinite")
def read_default_settings() -> SettingsIO:
    """I valori dei dati iniziali, per "Ripristina predefiniti"."""
    return SettingsIO.model_validate(get_default_settings())


@router.put("/settings", response_model=SettingsIO, summary="Sostituisce le impostazioni")
def put_settings(request: Request, body: SettingsIO) -> SettingsIO:
    """Effetto immediato sulle analisi; la generazione già fatta non cambia finché non si
    rigenera."""
    return SettingsIO.model_validate(replace_settings(_engine(request), body.model_dump()))
