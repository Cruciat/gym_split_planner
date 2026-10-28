"""Conversione dal database agli oggetti del dominio (ADR 0005)."""

from collections import defaultdict
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, aliased, load_only, selectinload

from gym_split_planner.db.models import (
    AppSetting,
    DayTemplate,
    Equipment,
    Exercise,
    ExerciseMuscle,
    ExerciseTag,
    MovementFamily,
    Muscle,
    MuscleGroup,
    Plan,
    PlanDay,
    PlanDayStretch,
    PlanSlot,
    SplitTemplate,
    Tag,
)
from gym_split_planner.domain.duration import DurationParams
from gym_split_planner.domain.enums import Confidence, Kind, Level, Priority, Stretch, TagEffect
from gym_split_planner.domain.model import (
    Catalog,
    Day,
    ExerciseInfo,
    LevelWeights,
    MuscleTarget,
    PlanShape,
    Slot,
    TagRule,
)
from gym_split_planner.domain.scoring import ScoreWeights


def load_catalog(session: Session) -> Catalog:
    """Tutto il catalogo che serve ai calcoli, compresi gli esercizi disattivati.

    Si leggono solo le colonne che servono, senza costruire oggetti ORM: il catalogo
    si carica a ogni modifica di una scheda e deve costare pochi millisecondi (C10).
    """
    primary = aliased(MovementFamily)
    secondary = aliased(MovementFamily)
    rows = session.execute(
        select(
            Exercise.id,
            Exercise.code,
            primary.code,
            secondary.code,
            Exercise.family_rank,
            Equipment.code,
            Exercise.kind,
            Exercise.stretch,
            Exercise.confidence,
            Exercise.is_active,
            MuscleGroup.code,
        )
        .join(primary, Exercise.primary_family_id == primary.id)
        .outerjoin(secondary, Exercise.secondary_family_id == secondary.id)
        .join(MuscleGroup, primary.muscle_group_id == MuscleGroup.id)
        .join(Equipment, Exercise.equipment_id == Equipment.id)
    ).all()

    muscles_of: dict[int, dict[str, Level]] = defaultdict(dict)
    for exercise_id, muscle_code, level in session.execute(
        select(ExerciseMuscle.exercise_id, Muscle.code, ExerciseMuscle.level).join(
            Muscle, ExerciseMuscle.muscle_id == Muscle.id
        )
    ):
        muscles_of[exercise_id][muscle_code] = Level(level)
    tags_of: dict[int, set[str]] = defaultdict(set)
    for exercise_id, tag_code in session.execute(
        select(ExerciseTag.exercise_id, Tag.code).join(Tag, ExerciseTag.tag_id == Tag.id)
    ):
        tags_of[exercise_id].add(tag_code)

    infos = [
        ExerciseInfo(
            code=code,
            primary_family=primary_code,
            secondary_family=secondary_code,
            family_rank=rank,
            equipment=equipment,
            kind=Kind(kind),
            stretch=Stretch(stretch),
            confidence=Confidence(confidence),
            muscles=muscles_of[exercise_id],
            tags=frozenset(tags_of[exercise_id]),
            is_active=bool(active),
            group=group,
        )
        for (
            exercise_id,
            code,
            primary_code,
            secondary_code,
            rank,
            equipment,
            kind,
            stretch,
            confidence,
            active,
            group,
        ) in rows
    ]
    muscles = [
        MuscleTarget(code, Priority(priority), low, high)
        for code, priority, low, high in session.execute(
            select(Muscle.code, Muscle.priority, Muscle.weekly_min, Muscle.weekly_max).order_by(
                Muscle.sort_order
            )
        )
    ]
    tags = [
        TagRule(code, TagEffect(effect), points)
        for code, effect, points in session.execute(select(Tag.code, Tag.effect, Tag.points))
    ]
    return Catalog.build(infos, muscles, tags)


def load_split_shape(session: Session, code: str) -> PlanShape:
    """Giorni e slot di uno split predefinito, con gli esercizi ancora da scegliere."""
    split = session.scalars(
        select(SplitTemplate)
        .where(SplitTemplate.code == code)
        .options(selectinload(SplitTemplate.days).selectinload(DayTemplate.slots))
    ).one()
    return PlanShape(
        tuple(
            Day(
                day.code,
                day.times_per_week,
                tuple(
                    Slot(
                        family=slot.family.code,
                        sets=slot.default_sets,
                        rep_min=slot.rep_min,
                        rep_max=slot.rep_max,
                        optional=slot.is_optional,
                        weekly_weight=slot.weekly_weight,
                    )
                    for slot in day.slots
                ),
            )
            for day in split.days
        )
    )


def _setting(session: Session, key: str) -> Any:
    row = session.get(AppSetting, key)
    return row.value if row is not None else None


def load_level_weights(session: Session) -> LevelWeights:
    value = _setting(session, "level_weights") or {}
    return LevelWeights(float(value.get("P", 1.0)), float(value.get("S", 0.5)))


def load_score_weights(session: Session) -> ScoreWeights:
    value = _setting(session, "score_weights") or {}
    return ScoreWeights(**{k: float(v) for k, v in value.items()})


def load_session_cap(session: Session) -> float:
    value = _setting(session, "session_cap")
    return float(value) if isinstance(value, int | float) else 10.0


def load_duration_params(session: Session) -> DurationParams:
    value = _setting(session, "duration_params") or {}
    known = DurationParams.__dataclass_fields__
    return DurationParams(**{k: float(v) for k, v in value.items() if k in known})


def load_effort(session: Session) -> tuple[str, bool]:
    """RIR obiettivo e ultima serie a cedimento (``app_setting.effort``)."""
    value = _setting(session, "effort") or {}
    return str(value.get("rir", "0-2")), bool(value.get("failure_last_set", True))


def equipment_order(session: Session) -> tuple[str, ...]:
    """Codici degli attrezzi nell'ordine del catalogo: l'ordine predefinito delle preferenze."""
    return tuple(session.scalars(select(Equipment.code).order_by(Equipment.sort_order)))


# --- Schede ------------------------------------------------------------------------


def plan_query() -> Select[Plan]:
    """Scheda con tutto ciò che serve alla sua vista completa, in poche query."""
    # La vista della scheda non usa date e note degli esercizi: non si leggono.
    exercise_options = (
        load_only(
            Exercise.id,
            Exercise.code,
            Exercise.name,
            Exercise.equipment_id,
            Exercise.kind,
            Exercise.is_active,
        ),
        selectinload(Exercise.tags).selectinload(ExerciseTag.tag),
        selectinload(Exercise.equipment),
    )
    slots = selectinload(Plan.days).selectinload(PlanDay.slots)
    return select(Plan).options(
        selectinload(Plan.split_template),
        slots.selectinload(PlanSlot.family),
        slots.selectinload(PlanSlot.exercise).options(*exercise_options),
        slots.selectinload(PlanSlot.second_exercise).options(*exercise_options),
        selectinload(Plan.days)
        .selectinload(PlanDay.stretches)
        .selectinload(PlanDayStretch.stretch),
    )


def load_plan(session: Session, plan_id: int) -> Plan | None:
    return session.scalars(plan_query().where(Plan.id == plan_id)).one_or_none()


def day_code(day: PlanDay) -> str:
    """Nel dominio i giorni si riconoscono per codice: per una scheda è l'``id``."""
    return str(day.id)


def plan_shape(plan: Plan) -> PlanShape:
    """La scheda nella forma del dominio: giorni e slot in ordine, esercizi per ``code``."""
    return PlanShape(
        tuple(
            Day(
                day_code(day),
                day.times_per_week,
                tuple(
                    Slot(
                        family=slot.family.code,
                        sets=slot.sets,
                        rep_min=slot.rep_min,
                        rep_max=slot.rep_max,
                        exercise=slot.exercise.code if slot.exercise else None,
                        second_exercise=(
                            slot.second_exercise.code if slot.second_exercise else None
                        ),
                        optional=slot.is_optional,
                        weekly_weight=slot.weekly_weight,
                        locked=slot.locked,
                    )
                    for slot in day.slots
                ),
            )
            for day in plan.days
        )
    )
