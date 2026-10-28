"""Vincoli nel database e regole di cancellazione (modello dati, § 6 e § 7)."""

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import Session

from gym_split_planner.db.models import (
    Equipment,
    Exercise,
    ExerciseMuscle,
    ExerciseTag,
    MovementFamily,
    Muscle,
    MuscleGroup,
    Plan,
    PlanDay,
    PlanSlot,
    SplitTemplate,
    Tag,
)
from gym_split_planner.domain.enums import (
    Confidence,
    Kind,
    Level,
    Priority,
    Stretch,
    TagColor,
    TagEffect,
)


@dataclass
class Catalog:
    group: MuscleGroup
    muscle: Muscle
    family: MovementFamily
    other_family: MovementFamily
    equipment: Equipment
    exercise: Exercise


@pytest.fixture
def catalog(session: Session) -> Catalog:
    group = MuscleGroup(code="chest", name="Petto", sort_order=1)
    muscle = Muscle(
        code="chest-upper",
        name="Petto alto",
        short_name="Petto alto",
        group=group,
        priority=Priority.PRIORITY,
        weekly_min=10,
        weekly_max=18,
        sort_order=1,
    )
    equipment = Equipment(code="machine", name="Macchina", sort_order=1)
    session.add_all([group, muscle, equipment])
    session.flush()
    family = MovementFamily(
        code="press-incline", name="Spinta inclinata", muscle_group_id=group.id, sort_order=1
    )
    other = MovementFamily(
        code="fly-low-high", name="Croce dal basso", muscle_group_id=group.id, sort_order=2
    )
    session.add_all([family, other])
    session.flush()
    exercise = Exercise(
        code="chest-press-incline",
        name="Chest press inclinata",
        primary_family=family,
        family_rank=1,
        equipment=equipment,
        kind=Kind.COMPOUND,
        stretch=Stretch.MEDIUM,
        confidence=Confidence.LIMITED,
    )
    exercise.muscles.append(ExerciseMuscle(muscle=muscle, level=Level.PRIMARY))
    session.add(exercise)
    session.commit()
    return Catalog(group, muscle, family, other, equipment, exercise)


def _plan_with_slot(session: Session, catalog: Catalog, **plan: object) -> Plan:
    new_plan = Plan(name="Prova", preferences={"version": 2}, **plan)
    day = PlanDay(name="Push", position=1, times_per_week=2)
    day.slots.append(
        PlanSlot(
            position=1,
            family_id=catalog.family.id,
            exercise_id=catalog.exercise.id,
            sets=3,
            rep_min=6,
            rep_max=12,
        )
    )
    new_plan.days.append(day)
    session.add(new_plan)
    session.commit()
    return new_plan


# --- Valori e vincoli su una riga ---------------------------------------------------


def test_exercise_defaults_and_timestamps(catalog: Catalog) -> None:
    exercise = catalog.exercise

    assert exercise.is_active is True
    assert exercise.created_at.tzinfo is UTC
    assert exercise.updated_at >= exercise.created_at


def test_muscle_without_target_has_no_band(session: Session, catalog: Catalog) -> None:
    session.add(
        Muscle(
            code="chest-lower",
            name="Petto basso",
            short_name="Petto basso",
            muscle_group_id=catalog.group.id,
            priority=Priority.NONE,
            weekly_min=6,
            weekly_max=10,
            sort_order=2,
        )
    )
    with pytest.raises(IntegrityError, match="ck_muscle_band"):
        session.commit()


@pytest.mark.parametrize(("weekly_min", "weekly_max"), [(None, None), (10, 10), (12, 10), (-1, 5)])
def test_muscle_with_target_needs_a_valid_band(
    session: Session, catalog: Catalog, weekly_min: float | None, weekly_max: float | None
) -> None:
    catalog.muscle.weekly_min = weekly_min
    catalog.muscle.weekly_max = weekly_max
    with pytest.raises(IntegrityError, match="ck_muscle_band"):
        session.commit()


def test_enum_values_are_checked(session: Session, catalog: Catalog) -> None:
    catalog.muscle.priority = "altissima"  # type: ignore[assignment]
    with pytest.raises(StatementError):
        session.commit()


def test_secondary_family_differs_from_primary(session: Session, catalog: Catalog) -> None:
    catalog.exercise.secondary_family_id = catalog.family.id
    with pytest.raises(IntegrityError, match="ck_exercise_secondary_family"):
        session.commit()


@pytest.mark.parametrize("effect", [TagEffect.BONUS, TagEffect.PENALTY])
def test_bonus_and_penalty_need_points(session: Session, effect: TagEffect) -> None:
    session.add(
        Tag(
            code="t",
            name="Prova",
            symbol="warning",
            color=TagColor.WARNING,
            effect=effect,
            points=0,
            sort_order=1,
        )
    )
    with pytest.raises(IntegrityError, match="ck_tag_points_for_effect"):
        session.commit()


def test_slot_sets_and_reps_are_checked(session: Session, catalog: Catalog) -> None:
    plan = _plan_with_slot(session, catalog)
    slot = plan.days[0].slots[0]

    slot.sets = 9
    with pytest.raises(IntegrityError, match="ck_plan_slot_sets"):
        session.commit()
    session.rollback()

    slot.rep_min, slot.rep_max = 12, 6
    with pytest.raises(IntegrityError, match="ck_plan_slot_reps"):
        session.commit()


def test_times_per_week_between_one_and_three(session: Session, catalog: Catalog) -> None:
    plan = _plan_with_slot(session, catalog)
    plan.days[0].times_per_week = 4
    with pytest.raises(IntegrityError, match="ck_plan_day_times_per_week"):
        session.commit()


def test_only_one_active_plan(session: Session, catalog: Catalog) -> None:
    _plan_with_slot(session, catalog, is_active=True)
    _plan_with_slot(session, catalog, is_active=False)

    session.add(Plan(name="Altra", preferences={}, is_active=True))
    with pytest.raises(IntegrityError, match=r"plan\.is_active"):
        session.commit()


def test_naive_datetime_is_rejected(session: Session, catalog: Catalog) -> None:
    catalog.exercise.updated_at = datetime(2026, 10, 28, 9, 15)
    with pytest.raises(StatementError, match="senza fuso orario"):
        session.commit()


# --- Regole di cancellazione ---------------------------------------------------------


def test_exercise_used_in_a_plan_cannot_be_deleted(session: Session, catalog: Catalog) -> None:
    _plan_with_slot(session, catalog)

    with pytest.raises(IntegrityError, match="FOREIGN KEY"):
        session.execute(delete(Exercise).where(Exercise.id == catalog.exercise.id))


def test_deleting_an_exercise_removes_its_links(session: Session, catalog: Catalog) -> None:
    tag = Tag(
        code="neck-caution",
        name="Collo: attenzione",
        symbol="warning",
        color=TagColor.WARNING,
        effect=TagEffect.PENALTY,
        points=3,
        sort_order=1,
    )
    session.add(tag)
    session.flush()
    session.add(ExerciseTag(exercise_id=catalog.exercise.id, tag_id=tag.id, note="nota"))
    session.commit()

    session.execute(delete(Exercise).where(Exercise.id == catalog.exercise.id))
    session.commit()

    assert session.scalars(select(ExerciseMuscle)).all() == []
    assert session.scalars(select(ExerciseTag)).all() == []


def test_family_used_by_an_exercise_cannot_be_deleted(session: Session, catalog: Catalog) -> None:
    with pytest.raises(IntegrityError, match="FOREIGN KEY"):
        session.execute(delete(MovementFamily).where(MovementFamily.id == catalog.family.id))


def test_deleting_a_secondary_family_clears_it(session: Session, catalog: Catalog) -> None:
    catalog.exercise.secondary_family_id = catalog.other_family.id
    session.commit()

    session.execute(delete(MovementFamily).where(MovementFamily.id == catalog.other_family.id))
    session.commit()
    session.refresh(catalog.exercise)

    assert catalog.exercise.secondary_family_id is None


def test_deleting_a_plan_removes_days_and_slots(session: Session, catalog: Catalog) -> None:
    plan = _plan_with_slot(session, catalog)

    session.execute(delete(Plan).where(Plan.id == plan.id))
    session.commit()

    assert session.scalars(select(PlanDay)).all() == []
    assert session.scalars(select(PlanSlot)).all() == []


def test_deleting_a_split_keeps_its_plans(session: Session, catalog: Catalog) -> None:
    split = SplitTemplate(code="ppl-3", name="PPL 3", is_builtin=False, sort_order=1)
    session.add(split)
    session.flush()
    plan = _plan_with_slot(session, catalog, split_template_id=split.id)

    session.execute(delete(SplitTemplate).where(SplitTemplate.id == split.id))
    session.commit()
    session.refresh(plan)

    assert plan.split_template_id is None
    assert len(plan.days) == 1
