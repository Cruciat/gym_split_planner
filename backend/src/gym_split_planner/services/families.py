"""Famiglie di movimento: creazione, modifica, utilizzi, eliminazione (US-06; API, § 6.3)."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from gym_split_planner.db.models import (
    Exercise,
    MovementFamily,
    MuscleGroup,
    Plan,
    PlanDay,
    PlanSlot,
    SlotTemplate,
)
from gym_split_planner.db.session import make_session_factory
from gym_split_planner.services.catalog import FamilyData
from gym_split_planner.services.common import name_taken, new_code, next_sort_order, unknown
from gym_split_planner.services.errors import (
    InUseError,
    NotFoundError,
    RuleError,
    RuleViolationError,
)
from gym_split_planner.services.exercises import PlanUsageData

EDITABLE = frozenset({"name", "description", "muscle_group_id", "sort_order"})


@dataclass(frozen=True)
class FamilyInput:
    name: str
    description: str | None
    muscle_group_id: int


@dataclass(frozen=True)
class FamilyUsageData:
    """Chi usa una famiglia (API, § 6.3, "Utilizzi")."""

    exercises: int
    """Esercizi che la hanno come famiglia principale: ne impediscono l'eliminazione."""
    secondary_exercises: int
    """Esercizi che la hanno come secondaria: eliminandola, la perdono."""
    split_slots: int
    plans: tuple[PlanUsageData, ...]

    @property
    def blocks_deletion(self) -> bool:
        return self.exercises > 0 or self.split_slots > 0 or bool(self.plans)


def create_family(engine: Engine, data: FamilyInput, code: str | None = None) -> FamilyData:
    """Crea una famiglia in fondo all'elenco."""
    with make_session_factory(engine)() as session:
        errors = _check(session, data.name, data.muscle_group_id, exclude_id=None)
        family_code, code_errors = new_code(session, MovementFamily.code, data.name, code)
        errors += code_errors
        if errors:
            raise RuleViolationError(tuple(errors))
        family = MovementFamily(
            code=family_code,
            name=data.name,
            description=data.description,
            muscle_group_id=data.muscle_group_id,
            sort_order=next_sort_order(session, MovementFamily.sort_order),
        )
        session.add(family)
        session.commit()
        return _data(family)


def update_family(engine: Engine, family_id: int, changes: Mapping[str, Any]) -> FamilyData:
    """Modifica parziale: nome, descrizione, gruppo, ordine. Il ``code`` non cambia."""
    _only_editable(changes)
    with make_session_factory(engine)() as session:
        family = _load(session, family_id)
        name = changes.get("name", family.name)
        group_id = changes.get("muscle_group_id", family.muscle_group_id)
        errors = _check(session, name, group_id, exclude_id=family_id)
        if errors:
            raise RuleViolationError(tuple(errors))
        for field, value in changes.items():
            setattr(family, field, value)
        session.commit()
        return _data(family)


def get_family_usage(engine: Engine, family_id: int) -> FamilyUsageData:
    with make_session_factory(engine)() as session:
        _load(session, family_id)
        return _usage(session, family_id)


def delete_family(engine: Engine, family_id: int) -> None:
    """Elimina una famiglia non usata; dove era secondaria, gli esercizi la perdono."""
    with make_session_factory(engine)() as session:
        family = _load(session, family_id)
        usage = _usage(session, family_id)
        if usage.blocks_deletion:
            raise InUseError("Famiglia in uso", _usage_text(usage), _usage_json(usage))
        session.delete(family)
        session.commit()


# --- Dettagli --------------------------------------------------------------------


def _only_editable(changes: Mapping[str, Any]) -> None:
    unknown_fields = set(changes) - EDITABLE
    if unknown_fields:
        raise ValueError(f"Campi non modificabili: {sorted(unknown_fields)}")


def _load(session: Session, family_id: int) -> MovementFamily:
    family = session.get(MovementFamily, family_id)
    if family is None:
        raise NotFoundError("Famiglia non trovata", f"Non esiste la famiglia {family_id}.")
    return family


def _check(session: Session, name: str, group_id: int, exclude_id: int | None) -> list[RuleError]:
    errors: list[RuleError] = []
    if session.get(MuscleGroup, group_id) is None:
        errors.append(unknown("muscle_group_id", "Il gruppo muscolare non esiste."))
    if name_taken(session, MovementFamily.name, MovementFamily.id, name, exclude_id):
        errors.append(RuleError("name-taken", "name", f"Esiste già una famiglia «{name}»."))
    return errors


def _count(session: Session, query: Any) -> int:
    return int(session.scalar(query) or 0)


def _usage(session: Session, family_id: int) -> FamilyUsageData:
    plans = session.execute(
        select(Plan.id, Plan.name, func.count(PlanSlot.id))
        .join(PlanDay, PlanDay.plan_id == Plan.id)
        .join(PlanSlot, PlanSlot.plan_day_id == PlanDay.id)
        .where(PlanSlot.family_id == family_id)
        .group_by(Plan.id, Plan.name)
        .order_by(Plan.name)
    ).all()
    count = select(func.count())
    return FamilyUsageData(
        exercises=_count(
            session, count.select_from(Exercise).where(Exercise.primary_family_id == family_id)
        ),
        secondary_exercises=_count(
            session, count.select_from(Exercise).where(Exercise.secondary_family_id == family_id)
        ),
        split_slots=_count(
            session, count.select_from(SlotTemplate).where(SlotTemplate.family_id == family_id)
        ),
        plans=tuple(PlanUsageData(id_, name, slots) for id_, name, slots in plans),
    )


def _usage_json(usage: FamilyUsageData) -> dict[str, Any]:
    return {
        "exercises": usage.exercises,
        "secondary_exercises": usage.secondary_exercises,
        "split_slots": usage.split_slots,
        "plans": [{"id": p.id, "name": p.name, "slots": p.slots} for p in usage.plans],
    }


def _usage_text(usage: FamilyUsageData) -> str:
    parts = []
    if usage.exercises:
        parts.append(f"{usage.exercises} esercizi la hanno come famiglia principale")
    if usage.split_slots:
        parts.append(f"{usage.split_slots} slot degli split predefiniti la chiedono")
    if usage.plans:
        names = ", ".join(f"«{p.name}»" for p in usage.plans)
        parts.append(f"è usata nelle schede {names}")
    return "Non si può eliminare: " + "; ".join(parts) + "."


def _data(family: MovementFamily) -> FamilyData:
    return FamilyData(
        id=family.id,
        code=family.code,
        name=family.name,
        description=family.description,
        muscle_group_id=family.muscle_group_id,
        sort_order=family.sort_order,
    )
