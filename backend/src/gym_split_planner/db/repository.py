"""Conversione dal database agli oggetti del dominio (ADR 0005)."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from gym_split_planner.db.models import (
    AppSetting,
    DayTemplate,
    Exercise,
    ExerciseMuscle,
    ExerciseTag,
    Muscle,
    SplitTemplate,
    Tag,
)
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
    """Tutto il catalogo che serve ai calcoli, compresi gli esercizi disattivati."""
    exercises = session.scalars(
        select(Exercise).options(
            selectinload(Exercise.primary_family),
            selectinload(Exercise.secondary_family),
            selectinload(Exercise.equipment),
            selectinload(Exercise.muscles).selectinload(ExerciseMuscle.muscle),
            selectinload(Exercise.tags).selectinload(ExerciseTag.tag),
        )
    )
    infos = [
        ExerciseInfo(
            code=e.code,
            primary_family=e.primary_family.code,
            secondary_family=e.secondary_family.code if e.secondary_family else None,
            family_rank=e.family_rank,
            equipment=e.equipment.code,
            kind=e.kind,
            stretch=e.stretch,
            confidence=e.confidence,
            muscles={link.muscle.code: link.level for link in e.muscles},
            tags=frozenset(link.tag.code for link in e.tags),
            is_active=e.is_active,
        )
        for e in exercises
    ]
    muscles = [
        MuscleTarget(m.code, m.priority, m.weekly_min, m.weekly_max)
        for m in session.scalars(select(Muscle).order_by(Muscle.sort_order))
    ]
    tags = [TagRule(t.code, t.effect, t.points) for t in session.scalars(select(Tag))]
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
