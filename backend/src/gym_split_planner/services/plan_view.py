"""La scheda completa con l'analisi (API, § 7), costruita in un solo punto.

Tutte le risposte che restituiscono una scheda passano da ``build_plan_view``: così
la forma non può divergere tra un endpoint e l'altro (API, § 9). I calcoli sono del
dominio; qui si convertono codici in ``id`` e si aggiungono i valori derivati che
servono a schermata e PDF (recupero, RIR, cedimento).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from gym_split_planner.db.models import (
    Exercise,
    MovementFamily,
    Muscle,
    MuscleGroup,
    Plan,
    PlanDay,
)
from gym_split_planner.db.repository import (
    day_code,
    equipment_order,
    load_catalog,
    load_duration_params,
    load_effort,
    load_level_weights,
    load_session_cap,
    plan_shape,
)
from gym_split_planner.domain.analysis import AnalysisSettings, analyze
from gym_split_planner.domain.duration import DurationParams, rest_seconds
from gym_split_planner.domain.enums import Kind
from gym_split_planner.domain.preferences import plan_preferences


@dataclass(frozen=True)
class SplitRefData:
    id: int
    code: str
    name: str


@dataclass(frozen=True)
class BadgeData:
    """Simbolo di un'etichetta visibile su un esercizio, con la nota dell'assegnazione."""

    tag_id: int
    code: str
    name: str
    symbol: str
    color: str
    note: str | None


@dataclass(frozen=True)
class SlotExerciseData:
    id: int
    code: str
    name: str
    equipment: str
    kind: str
    is_active: bool
    badges: tuple[BadgeData, ...]


@dataclass(frozen=True)
class FamilyRefData:
    id: int
    code: str
    name: str


@dataclass(frozen=True)
class SlotData:
    id: int
    position: int
    family: FamilyRefData
    exercise: SlotExerciseData | None
    second_exercise: SlotExerciseData | None
    sets: int
    rep_min: int
    rep_max: int
    is_optional: bool
    weekly_weight: float
    locked: bool
    note: str | None
    rest_seconds: int | None
    """Derivato dal tipo dell'esercizio (``duration_params``): non si salva."""
    rir: str | None
    last_set_to_failure: bool | None


@dataclass(frozen=True)
class DayStretchData:
    id: int
    code: str
    name: str
    dose: str


@dataclass(frozen=True)
class DayData:
    id: int
    name: str
    position: int
    times_per_week: int
    stretches: tuple[DayStretchData, ...]
    slots: tuple[SlotData, ...]


@dataclass(frozen=True)
class VolumeData:
    muscle_id: int
    code: str
    name: str
    short_name: str
    group_code: str
    volume: float
    priority: str
    weekly_min: float | None
    weekly_max: float | None
    status: str | None
    overridden: bool


@dataclass(frozen=True)
class MuscleVolumeRef:
    muscle_id: int
    volume: float


@dataclass(frozen=True)
class SessionData:
    day_id: int
    session: int
    minutes: float
    max_muscle_volume: MuscleVolumeRef | None


@dataclass(frozen=True)
class WarningData:
    """Avviso della scheda (algoritmo, § 8): i campi valorizzati dipendono dal ``code``."""

    code: str
    day_id: int | None = None
    session: int | None = None
    slot_id: int | None = None
    position: int | None = None
    family_id: int | None = None
    muscle_id: int | None = None
    volume: float | None = None
    weekly_min: float | None = None
    weekly_max: float | None = None
    minutes: float | None = None
    excluded_by: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnalysisData:
    volumes: tuple[VolumeData, ...]
    sessions: tuple[SessionData, ...]
    warnings: tuple[WarningData, ...]


@dataclass(frozen=True)
class PlanViewData:
    id: int
    name: str
    revision: int
    is_active: bool
    split: SplitRefData | None
    created_at: datetime
    updated_at: datetime
    preferences: dict[str, Any]
    days: tuple[DayData, ...]
    analysis: AnalysisData


def build_plan_view(session: Session, plan: Plan) -> PlanViewData:
    """Scheda completa, con analisi calcolata sui valori effettivi (API, § 7)."""
    catalog = load_catalog(session)
    preferences = plan_preferences(plan.preferences, equipment_order(session))
    duration = load_duration_params(session)
    rir, failure_last_set = load_effort(session)
    analysis = analyze(
        plan_shape(plan),
        catalog,
        preferences.scoring,
        AnalysisSettings(
            level_weights=load_level_weights(session),
            session_cap=load_session_cap(session),
            duration=duration,
            max_session_minutes=preferences.max_session_minutes,
        ),
    )

    muscles = {
        row.code: row
        for row in session.execute(
            select(
                Muscle.id,
                Muscle.code,
                Muscle.name,
                Muscle.short_name,
                MuscleGroup.code.label("group"),
            ).join(MuscleGroup, Muscle.muscle_group_id == MuscleGroup.id)
        )
    }
    families: dict[str, int] = dict(
        session.execute(select(MovementFamily.code, MovementFamily.id)).all()
    )
    days_by_code = {day_code(day): day for day in plan.days}

    def slot_of(day: PlanDay | None, position: int | None) -> int | None:
        if day is None or position is None or not 1 <= position <= len(day.slots):
            return None
        return day.slots[position - 1].id

    volumes = tuple(
        VolumeData(
            muscle_id=muscles[v.muscle].id,
            code=v.muscle,
            name=muscles[v.muscle].name,
            short_name=muscles[v.muscle].short_name,
            group_code=muscles[v.muscle].group,
            volume=v.volume,
            priority=v.target.priority,
            weekly_min=v.target.weekly_min,
            weekly_max=v.target.weekly_max,
            status=v.status,
            overridden=v.overridden,
        )
        for v in analysis.volumes
    )
    targets = {v.muscle: v.target for v in analysis.volumes}
    sessions = tuple(
        SessionData(
            day_id=days_by_code[s.day].id,
            session=s.session,
            minutes=s.minutes,
            max_muscle_volume=(
                MuscleVolumeRef(muscles[s.max_muscle].id, s.max_volume) if s.max_muscle else None
            ),
        )
        for s in analysis.sessions
    )
    warnings = tuple(
        WarningData(
            code=w.code,
            day_id=days_by_code[w.day].id if w.day else None,
            session=w.session,
            slot_id=slot_of(days_by_code.get(w.day or ""), w.position),
            position=w.position,
            family_id=families.get(w.family) if w.family else None,
            muscle_id=muscles[w.muscle].id if w.muscle else None,
            volume=w.volume,
            weekly_min=targets[w.muscle].weekly_min if w.muscle in targets else None,
            weekly_max=targets[w.muscle].weekly_max if w.muscle in targets else None,
            minutes=w.minutes,
            excluded_by=w.excluded_by,
        )
        for w in analysis.warnings
    )

    split = plan.split_template
    return PlanViewData(
        id=plan.id,
        name=plan.name,
        revision=plan.revision,
        is_active=plan.is_active,
        split=SplitRefData(split.id, split.code, split.name) if split else None,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        preferences=plan.preferences,
        days=tuple(_day(day, duration, rir, failure_last_set) for day in plan.days),
        analysis=AnalysisData(volumes, sessions, warnings),
    )


def _day(day: PlanDay, duration: DurationParams, rir: str, failure_last_set: bool) -> DayData:
    return DayData(
        id=day.id,
        name=day.name,
        position=day.position,
        times_per_week=day.times_per_week,
        stretches=tuple(
            DayStretchData(link.stretch.id, link.stretch.code, link.stretch.name, link.stretch.dose)
            for link in day.stretches
        ),
        slots=tuple(
            SlotData(
                id=slot.id,
                position=slot.position,
                family=FamilyRefData(slot.family.id, slot.family.code, slot.family.name),
                exercise=_exercise(slot.exercise),
                second_exercise=_exercise(slot.second_exercise),
                sets=slot.sets,
                rep_min=slot.rep_min,
                rep_max=slot.rep_max,
                is_optional=slot.is_optional,
                weekly_weight=slot.weekly_weight,
                locked=slot.locked,
                note=slot.note,
                rest_seconds=(
                    round(rest_seconds(Kind(slot.exercise.kind), duration))
                    if slot.exercise
                    else None
                ),
                rir=rir if slot.exercise else None,
                last_set_to_failure=(
                    failure_last_set
                    and (
                        slot.exercise.kind == Kind.ISOLATION
                        or slot.exercise.equipment.code == "machine"
                    )
                    if slot.exercise
                    else None
                ),
            )
            for slot in day.slots
        ),
    )


def _exercise(exercise: Exercise | None) -> SlotExerciseData | None:
    if exercise is None:
        return None
    links = sorted(
        (link for link in exercise.tags if link.tag.show_badge),
        key=lambda found: found.tag.sort_order,
    )
    return SlotExerciseData(
        id=exercise.id,
        code=exercise.code,
        name=exercise.name,
        equipment=exercise.equipment.code,
        kind=exercise.kind,
        is_active=exercise.is_active,
        badges=tuple(
            BadgeData(
                tag_id=link.tag.id,
                code=link.tag.code,
                name=link.tag.name,
                symbol=link.tag.symbol,
                color=link.tag.color,
                note=link.note,
            )
            for link in links
        ),
    )
