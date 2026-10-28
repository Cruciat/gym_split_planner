"""Modifica dei muscoli: nomi, priorità e fascia del catalogo (US-07; API, § 6.3).

I nuovi valori valgono subito per tutte le schede che non hanno personalizzato il
muscolo (CA3). Una scheda che lo ha personalizzato in parte (per esempio solo il
massimo) combina la sua personalizzazione con il catalogo: se la combinazione non
fosse più una fascia valida, la modifica è rifiutata con l'elenco delle schede
(``invalid-band``), invece di lasciarle in uno stato che non si può calcolare.
"""

from collections.abc import Mapping
from typing import Any

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from gym_split_planner.db.models import Muscle, Plan
from gym_split_planner.db.session import make_session_factory
from gym_split_planner.domain.catalog_rules import check_band, is_valid_target
from gym_split_planner.domain.enums import Priority
from gym_split_planner.domain.model import MuscleTarget
from gym_split_planner.domain.preferences import overrides_from_preferences
from gym_split_planner.domain.volume import resolve_muscle
from gym_split_planner.services.catalog import MuscleData
from gym_split_planner.services.errors import (
    InvalidBandError,
    NotFoundError,
    PlanRef,
    RuleError,
    RuleViolationError,
)

EDITABLE = frozenset({"name", "short_name", "priority", "weekly_min", "weekly_max", "notes"})


def update_muscle(engine: Engine, muscle_id: int, changes: Mapping[str, Any]) -> MuscleData:
    """Modifica parziale. Con "nessun obiettivo" la fascia si svuota da sola."""
    unknown_fields = set(changes) - EDITABLE
    if unknown_fields:
        raise ValueError(f"Campi non modificabili: {sorted(unknown_fields)}")
    with make_session_factory(engine)() as session:
        muscle = session.get(Muscle, muscle_id)
        if muscle is None:
            raise NotFoundError("Muscolo non trovato", f"Non esiste il muscolo {muscle_id}.")

        priority = Priority(changes.get("priority", muscle.priority))
        weekly_min: float | None = changes.get("weekly_min", muscle.weekly_min)
        weekly_max: float | None = changes.get("weekly_max", muscle.weekly_max)
        if priority is Priority.NONE:
            weekly_min = weekly_max = None

        violations = check_band(priority, weekly_min, weekly_max)
        if violations:
            raise RuleViolationError(
                tuple(RuleError(v.rule, v.field, v.message) for v in violations)
            )
        target = MuscleTarget(muscle.code, priority, weekly_min, weekly_max)
        broken = _plans_with_invalid_band(session, target)
        if broken:
            raise InvalidBandError(broken)

        for field in ("name", "short_name", "notes"):
            if field in changes:
                setattr(muscle, field, changes[field])
        muscle.priority = priority
        muscle.weekly_min = weekly_min
        muscle.weekly_max = weekly_max
        session.commit()
        return MuscleData(
            id=muscle.id,
            code=muscle.code,
            name=muscle.name,
            short_name=muscle.short_name,
            muscle_group_id=muscle.muscle_group_id,
            priority=muscle.priority,
            weekly_min=muscle.weekly_min,
            weekly_max=muscle.weekly_max,
            notes=muscle.notes,
            sort_order=muscle.sort_order,
        )


def _plans_with_invalid_band(session: Session, target: MuscleTarget) -> tuple[PlanRef, ...]:
    """Schede che personalizzano il muscolo e con il nuovo catalogo non sarebbero valide."""
    broken = []
    for plan in session.scalars(select(Plan).order_by(Plan.name)):
        overrides = overrides_from_preferences(plan.preferences)
        if target.code not in overrides.muscles:
            continue
        if not is_valid_target(resolve_muscle(target, overrides)):
            broken.append(PlanRef(plan.id, plan.name))
    return tuple(broken)
