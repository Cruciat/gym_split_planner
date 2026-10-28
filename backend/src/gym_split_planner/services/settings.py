"""Impostazioni globali (US-20; API, § 6.1): pesi, tetto per seduta, durata, intensità.

Valgono subito per le analisi di tutte le schede; la generazione già fatta non cambia
finché non si rigenera. I valori predefiniti sono quelli dei dati iniziali.
"""

from collections.abc import Mapping
from typing import Any

from sqlalchemy import Engine, select

from gym_split_planner.db.models import AppSetting
from gym_split_planner.db.seed.loader import default_settings
from gym_split_planner.db.session import make_session_factory

KEYS = (
    "level_weights",
    "session_cap",
    "score_weights",
    "duration_params",
    "warmup_text",
    "effort",
)


def get_settings(engine: Engine) -> dict[str, Any]:
    """Le impostazioni salvate; una chiave mancante prende il valore predefinito."""
    defaults = default_settings()
    with make_session_factory(engine)() as session:
        stored = {row.key: row.value for row in session.scalars(select(AppSetting))}
    return {key: stored.get(key, defaults[key]) for key in KEYS}


def get_default_settings() -> dict[str, Any]:
    defaults = default_settings()
    return {key: defaults[key] for key in KEYS}


def replace_settings(engine: Engine, settings: Mapping[str, Any]) -> dict[str, Any]:
    """Sostituisce tutte le impostazioni (già validate dallo strato api)."""
    unknown = set(settings) - set(KEYS)
    if unknown:
        raise ValueError(f"Impostazioni sconosciute: {sorted(unknown)}")
    with make_session_factory(engine)() as session:
        for key in KEYS:
            row = session.get(AppSetting, key)
            if row is None:
                session.add(AppSetting(key=key, value=settings[key]))
            else:
                row.value = settings[key]
        session.commit()
    return get_settings(engine)
