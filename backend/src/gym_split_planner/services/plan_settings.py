"""Preferenze e personalizzazioni di una scheda (US-11; API, § 6.6 e § 8.1).

La vista delle personalizzazioni dà, per ogni muscolo ed etichetta, i tre livelli:
valore del catalogo, personalizzazione della scheda, valore effettivo. Il client
mostra quello effettivo, segnala ciò che è personalizzato e sa a cosa tornerebbe il
ripristino, senza ricalcolare nulla.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from gym_split_planner.db.models import Muscle, MuscleGroup, Plan, Tag
from gym_split_planner.db.repository import equipment_order
from gym_split_planner.db.session import make_session_factory
from gym_split_planner.domain.model import MuscleTarget, TagRule
from gym_split_planner.domain.preferences import plan_preferences
from gym_split_planner.domain.volume import resolve_muscle, resolve_tag
from gym_split_planner.services.errors import NotFoundError
from gym_split_planner.services.plan_view import PlanViewData
from gym_split_planner.services.plans import modify_plan, validated_preferences


@dataclass(frozen=True)
class MuscleValuesData:
    priority: str | None = None
    weekly_min: float | None = None
    weekly_max: float | None = None


@dataclass(frozen=True)
class MuscleSettingData:
    muscle_id: int
    code: str
    name: str
    short_name: str
    group_code: str
    catalog: MuscleValuesData
    override: MuscleValuesData
    effective: MuscleValuesData


@dataclass(frozen=True)
class TagValuesData:
    effect: str | None = None
    points: float | None = None


@dataclass(frozen=True)
class TagSettingData:
    tag_id: int
    code: str
    name: str
    symbol: str
    color: str
    catalog: TagValuesData
    override: TagValuesData
    effective: TagValuesData


@dataclass(frozen=True)
class PlanSettingsData:
    name: str
    revision: int
    equipment_order: tuple[str, ...]
    max_session_minutes: float | None
    muscles: tuple[MuscleSettingData, ...]
    tags: tuple[TagSettingData, ...]


def get_plan_settings(engine: Engine, plan_id: int) -> PlanSettingsData:
    """Vista per la schermata delle preferenze (§ 8.1)."""
    with make_session_factory(engine)() as session:
        plan = session.get(Plan, plan_id)
        if plan is None:
            raise NotFoundError("Scheda non trovata", f"Non esiste la scheda {plan_id}.")
        prefs = plan_preferences(plan.preferences, equipment_order(session))
        stored = _stored_overrides(plan.preferences)
        return PlanSettingsData(
            name=plan.name,
            revision=plan.revision,
            equipment_order=prefs.equipment_order,
            max_session_minutes=prefs.max_session_minutes,
            muscles=_muscles(session, prefs.overrides, stored.get("muscles", {})),
            tags=_tags(session, prefs.overrides, stored.get("tags", {})),
        )


def set_preferences(
    engine: Engine, plan_id: int, preferences: Mapping[str, Any], expected_revision: int
) -> PlanViewData:
    """Sostituisce le preferenze, normalizzate e validate sui valori effettivi.

    Non rigenera la scheda: aggiorna solo l'analisi. Per applicare le nuove
    preferenze agli esercizi c'è la rigenerazione, che mostra prima le differenze.
    """

    def change(session: Session, plan: Plan) -> None:
        plan.preferences = validated_preferences(session, preferences)

    return modify_plan(engine, plan_id, expected_revision, change)


def _stored_overrides(preferences: Mapping[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    raw = preferences.get("overrides")
    if not isinstance(raw, dict):
        return {}
    return {
        key: {code: v for code, v in value.items() if isinstance(v, dict)}
        for key, value in raw.items()
        if isinstance(value, dict)
    }


def _muscles(
    session: Session, overrides: Any, stored: Mapping[str, Mapping[str, Any]]
) -> tuple[MuscleSettingData, ...]:
    rows = session.execute(
        select(
            Muscle.id,
            Muscle.code,
            Muscle.name,
            Muscle.short_name,
            MuscleGroup.code,
            Muscle.priority,
            Muscle.weekly_min,
            Muscle.weekly_max,
        )
        .join(MuscleGroup, Muscle.muscle_group_id == MuscleGroup.id)
        .order_by(Muscle.sort_order)
    )
    result = []
    for muscle_id, code, name, short_name, group, priority, low, high in rows:
        target = MuscleTarget(code, priority, low, high)
        effective = resolve_muscle(target, overrides)
        own = stored.get(code, {})
        result.append(
            MuscleSettingData(
                muscle_id=muscle_id,
                code=code,
                name=name,
                short_name=short_name,
                group_code=group,
                catalog=MuscleValuesData(priority, low, high),
                override=MuscleValuesData(
                    own.get("priority"), own.get("weekly_min"), own.get("weekly_max")
                ),
                effective=MuscleValuesData(
                    effective.priority, effective.weekly_min, effective.weekly_max
                ),
            )
        )
    return tuple(result)


def _tags(
    session: Session, overrides: Any, stored: Mapping[str, Mapping[str, Any]]
) -> tuple[TagSettingData, ...]:
    rows = session.execute(
        select(Tag.id, Tag.code, Tag.name, Tag.symbol, Tag.color, Tag.effect, Tag.points).order_by(
            Tag.sort_order
        )
    )
    result = []
    for tag_id, code, name, symbol, color, effect, points in rows:
        effective = resolve_tag(TagRule(code, effect, points), overrides)
        own = stored.get(code, {})
        result.append(
            TagSettingData(
                tag_id=tag_id,
                code=code,
                name=name,
                symbol=symbol,
                color=color,
                catalog=TagValuesData(effect, points),
                override=TagValuesData(own.get("effect"), own.get("points")),
                effective=TagValuesData(effective.effect, effective.points),
            )
        )
    return tuple(result)
