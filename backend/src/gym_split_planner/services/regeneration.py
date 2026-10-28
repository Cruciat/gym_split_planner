"""Rigenerazione di una scheda (US-18; algoritmo, § 4.2; API, § 6.9).

L'anteprima calcola le differenze tra la scheda e una nuova generazione con le
preferenze correnti, senza modificare nulla; l'applicazione cambia solo gli slot
scelti, dopo aver ricontrollato la revisione su cui l'anteprima era calcolata.
"""

from collections.abc import Collection
from dataclasses import dataclass

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from gym_split_planner.db.models import Exercise, Muscle, Plan
from gym_split_planner.db.repository import (
    day_code,
    equipment_order,
    load_catalog,
    load_level_weights,
    load_score_weights,
    plan_shape,
)
from gym_split_planner.db.session import make_session_factory
from gym_split_planner.domain.generation import SlotChange, regeneration_changes
from gym_split_planner.domain.preferences import plan_preferences
from gym_split_planner.domain.preview import main_exercise_delta
from gym_split_planner.services.errors import RuleError, RuleViolationError
from gym_split_planner.services.plan_candidates import VolumeDeltaData
from gym_split_planner.services.plan_view import PlanViewData
from gym_split_planner.services.plans import load_existing, modify_plan


@dataclass(frozen=True)
class ExerciseRefData:
    exercise_id: int
    name: str


@dataclass(frozen=True)
class RegenerationChangeData:
    slot_id: int
    day_id: int
    day_name: str
    position: int
    current: ExerciseRefData | None
    proposed: ExerciseRefData
    volume_delta: tuple[VolumeDeltaData, ...]


@dataclass(frozen=True)
class RegenerationPreviewData:
    revision: int
    """Revisione su cui è calcolata: va rimandata in ``If-Match`` per applicare."""
    changes: tuple[RegenerationChangeData, ...]
    locked_slots: int
    """Slot con il lucchetto, che la rigenerazione non tocca (wireframe § 3.6)."""


def preview_regeneration(engine: Engine, plan_id: int) -> RegenerationPreviewData:
    """Cosa cambierebbe rigenerando, con l'effetto sul volume di ogni cambio."""
    with make_session_factory(engine)() as session:
        plan = load_existing(session, plan_id)
        changes = _changes(session, plan)
        names = dict(session.execute(select(Exercise.code, Exercise.name)).all())
        ids: dict[str, int] = dict(session.execute(select(Exercise.code, Exercise.id)).all())
        muscles: dict[str, int] = dict(session.execute(select(Muscle.code, Muscle.id)).all())
        catalog = load_catalog(session)
        weights = load_level_weights(session)
        shape = {day.code: day for day in plan_shape(plan).days}
        days = {day_code(day): day for day in plan.days}
        result = []
        for change in changes:
            day = days[change.day]
            slot = day.slots[change.position - 1]
            delta = main_exercise_delta(
                shape[change.day], change.position, change.proposed, catalog, weights
            )
            result.append(
                RegenerationChangeData(
                    slot_id=slot.id,
                    day_id=day.id,
                    day_name=day.name,
                    position=change.position,
                    current=(
                        ExerciseRefData(ids[change.current], names[change.current])
                        if change.current
                        else None
                    ),
                    proposed=ExerciseRefData(ids[change.proposed], names[change.proposed]),
                    volume_delta=tuple(
                        VolumeDeltaData(muscles[code], code, value) for code, value in delta.items()
                    ),
                )
            )
        locked = sum(1 for day in plan.days for slot in day.slots if slot.locked)
        return RegenerationPreviewData(plan.revision, tuple(result), locked)


def apply_regeneration(
    engine: Engine, plan_id: int, slot_ids: Collection[int], expected_revision: int
) -> PlanViewData:
    """Applica le differenze degli slot scelti (tutti o una parte).

    Le differenze si ricalcolano con la stessa revisione dell'anteprima: se nel
    frattempo la scheda è cambiata, ``412`` e si ricalcola l'anteprima. Uno slot
    scelto che non ha più una differenza resta com'è. Se il nuovo esercizio coincide
    con la variante della seconda seduta, la variante si toglie.
    """
    chosen = set(slot_ids)

    def change(session: Session, plan: Plan) -> None:
        slots = {slot.id: (slot, day) for day in plan.days for slot in day.slots}
        if not chosen <= set(slots):
            raise RuleViolationError(
                (
                    RuleError(
                        "unknown-reference",
                        "slot_ids",
                        "Uno degli slot indicati non appartiene alla scheda.",
                    ),
                )
            )
        ids: dict[str, int] = dict(session.execute(select(Exercise.code, Exercise.id)).all())
        days = {day_code(day): day for day in plan.days}
        for found in _changes(session, plan):
            slot = days[found.day].slots[found.position - 1]
            if slot.id not in chosen:
                continue
            slot.exercise_id = ids[found.proposed]
            if slot.second_exercise_id == slot.exercise_id:
                slot.second_exercise_id = None

    return modify_plan(engine, plan_id, expected_revision, change)


def _changes(session: Session, plan: Plan) -> list[SlotChange]:
    prefs = plan_preferences(plan.preferences, equipment_order(session))
    return regeneration_changes(
        plan_shape(plan), load_catalog(session), prefs.scoring, load_score_weights(session)
    )
