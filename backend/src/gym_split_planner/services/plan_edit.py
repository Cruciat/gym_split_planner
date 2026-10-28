"""Giorni e slot di una scheda: aggiunta, modifica, eliminazione, ordine (API, § 6.7, § 6.8).

Ogni funzione è una modifica della scheda: passa da ``modify_plan`` (revisione,
risposta completa) e applica tutto o niente. Giorni e slot si cercano dentro la
scheda dell'URL: un ``id`` di un'altra scheda è un ``404`` (C4).
"""

from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from gym_split_planner.db.models import Exercise, MovementFamily, Plan, PlanDay, PlanSlot
from gym_split_planner.db.repository import (
    equipment_order,
    load_catalog,
    load_score_weights,
)
from gym_split_planner.domain.enums import Kind
from gym_split_planner.domain.model import Catalog
from gym_split_planner.domain.plan_rules import SlotState, check_slot, default_prescription
from gym_split_planner.domain.preferences import plan_preferences
from gym_split_planner.domain.scoring import best_candidate
from gym_split_planner.services.errors import NotFoundError, RuleError, RuleViolationError
from gym_split_planner.services.plan_view import PlanViewData
from gym_split_planner.services.plans import modify_plan

TEMPORARY_OFFSET = -10_000
"""Posizioni temporanee durante il riordino: lontane da quelle di un elemento appena aggiunto."""

SLOT_FIELDS = frozenset(
    {
        "exercise_id",
        "second_exercise_id",
        "family_id",
        "sets",
        "rep_min",
        "rep_max",
        "is_optional",
        "weekly_weight",
        "locked",
        "note",
    }
)


# --- Giorni (§ 6.7) ----------------------------------------------------------------


def add_day(
    engine: Engine,
    plan_id: int,
    name: str,
    times_per_week: int,
    position: int | None,
    expected_revision: int,
) -> PlanViewData:
    """Giorno nuovo, senza esercizi né stretching (US-21 CA1); senza posizione va in fondo."""

    def change(session: Session, plan: Plan) -> None:
        day = PlanDay(name=name, times_per_week=times_per_week, position=-len(plan.days) - 1)
        plan.days.append(day)
        session.flush()
        ordered = [d for d in plan.days if d is not day]
        ordered.insert(_index(position, len(ordered)), day)
        _renumber(session, ordered)

    return modify_plan(engine, plan_id, expected_revision, change)


def update_day(
    engine: Engine,
    plan_id: int,
    day_id: int,
    changes: Mapping[str, Any],
    expected_revision: int,
) -> PlanViewData:
    """Nome e volte a settimana. Scendendo a 1, le varianti della seconda seduta del
    giorno si tolgono nella stessa operazione (US-21 CA3)."""

    def change(_session: Session, plan: Plan) -> None:
        day = _day(plan, day_id)
        if "name" in changes:
            day.name = changes["name"]
        if "times_per_week" in changes:
            day.times_per_week = changes["times_per_week"]
            if day.times_per_week < 2:
                for slot in day.slots:
                    slot.second_exercise_id = None

    return modify_plan(engine, plan_id, expected_revision, change)


def delete_day(engine: Engine, plan_id: int, day_id: int, expected_revision: int) -> PlanViewData:
    """Elimina il giorno con i suoi slot; i giorni seguenti salgono di una posizione."""

    def change(session: Session, plan: Plan) -> None:
        day = _day(plan, day_id)
        plan.days.remove(day)
        session.delete(day)
        session.flush()
        _renumber(session, plan.days)

    return modify_plan(engine, plan_id, expected_revision, change)


def reorder_days(
    engine: Engine, plan_id: int, day_ids: Sequence[int], expected_revision: int
) -> PlanViewData:
    """Nuovo ordine dei giorni: tutti gli ``id`` della scheda, né uno di più né uno di meno."""

    def change(session: Session, plan: Plan) -> None:
        _renumber(session, _in_order(plan.days, day_ids, "day_ids"))

    return modify_plan(engine, plan_id, expected_revision, change)


# --- Slot (§ 6.8) ------------------------------------------------------------------


def add_slot(
    engine: Engine,
    plan_id: int,
    day_id: int,
    values: Mapping[str, Any],
    expected_revision: int,
) -> PlanViewData:
    """Slot nuovo in un giorno (US-16 CA3).

    Senza esercizio si assegna il miglior candidato della famiglia; senza serie e
    ripetizioni valgono quelle predefinite per il tipo di esercizio.
    """

    def change(session: Session, plan: Plan) -> None:
        day = _day(plan, day_id)
        family = _family(session, values["family_id"])
        catalog = load_catalog(session)
        codes = _exercise_codes(session)
        exercise_id = values.get("exercise_id")
        if exercise_id is None:
            exercise_id = _best(session, plan, catalog, family.code)
        kind = _kind(catalog, codes.get(exercise_id)) if exercise_id else None
        sets, rep_min, rep_max = default_prescription(kind)
        slot = PlanSlot(
            family_id=family.id,
            exercise_id=exercise_id,
            sets=values.get("sets") or sets,
            rep_min=values.get("rep_min") or rep_min,
            rep_max=values.get("rep_max") or rep_max,
            is_optional=False,
            weekly_weight=1.0,
            locked=False,
            position=-len(day.slots) - 1,
        )
        _check(slot, day, family.code, catalog, codes, changed={"exercise"})
        day.slots.append(slot)
        session.flush()
        ordered = [s for s in day.slots if s is not slot]
        ordered.insert(_index(values.get("position"), len(ordered)), slot)
        _renumber(session, ordered)

    return modify_plan(engine, plan_id, expected_revision, change)


def update_slot(
    engine: Engine,
    plan_id: int,
    slot_id: int,
    changes: Mapping[str, Any],
    expected_revision: int,
) -> PlanViewData:
    """Modifica parziale di uno slot, tutta o niente (US-14 → US-17).

    - Cambiando famiglia senza indicare l'esercizio, si assegna il miglior candidato
      della nuova famiglia; serie e ripetizioni restano; la variante della seconda
      seduta si toglie solo se coincidesse con il nuovo esercizio (US-16 CA5).
    - Il lucchetto protegge solo dalla rigenerazione: lo slot si modifica comunque.
    """
    unknown_fields = set(changes) - SLOT_FIELDS
    if unknown_fields:
        raise ValueError(f"Campi non modificabili: {sorted(unknown_fields)}")

    def change(session: Session, plan: Plan) -> None:
        slot, day = _slot(plan, slot_id)
        catalog = load_catalog(session)
        codes = _exercise_codes(session)
        family = _family(session, changes.get("family_id", slot.family_id))
        family_changed = family.id != slot.family_id

        exercise_id = changes.get("exercise_id", slot.exercise_id)
        if family_changed and "exercise_id" not in changes:
            exercise_id = _best(session, plan, catalog, family.code)
        second_id = changes.get("second_exercise_id", slot.second_exercise_id)
        if family_changed and "second_exercise_id" not in changes and second_id == exercise_id:
            second_id = None

        changed = set()
        if exercise_id != slot.exercise_id:
            changed.add("exercise")
        if second_id != slot.second_exercise_id:
            changed.add("second_exercise")

        for field in ("sets", "rep_min", "rep_max", "is_optional", "weekly_weight", "locked"):
            if field in changes:
                setattr(slot, field, changes[field])
        if "note" in changes:
            slot.note = changes["note"]
        slot.family_id = family.id
        slot.exercise_id = exercise_id
        slot.second_exercise_id = second_id
        _check(slot, day, family.code, catalog, codes, changed)

    return modify_plan(engine, plan_id, expected_revision, change)


def delete_slot(engine: Engine, plan_id: int, slot_id: int, expected_revision: int) -> PlanViewData:
    """Toglie lo slot; quelli seguenti salgono di una posizione."""

    def change(session: Session, plan: Plan) -> None:
        slot, day = _slot(plan, slot_id)
        day.slots.remove(slot)
        session.delete(slot)
        session.flush()
        _renumber(session, day.slots)

    return modify_plan(engine, plan_id, expected_revision, change)


def reorder_slots(
    engine: Engine,
    plan_id: int,
    day_id: int,
    slot_ids: Sequence[int],
    expected_revision: int,
) -> PlanViewData:
    """Nuovo ordine degli slot di un giorno (US-16 CA2)."""

    def change(session: Session, plan: Plan) -> None:
        day = _day(plan, day_id)
        _renumber(session, _in_order(day.slots, slot_ids, "slot_ids"))

    return modify_plan(engine, plan_id, expected_revision, change)


# --- Dettagli --------------------------------------------------------------------


def find_day(plan: Plan, day_id: int) -> PlanDay:
    return _day(plan, day_id)


def find_slot(plan: Plan, slot_id: int) -> tuple[PlanSlot, PlanDay]:
    return _slot(plan, slot_id)


def _day(plan: Plan, day_id: int) -> PlanDay:
    for day in plan.days:
        if day.id == day_id:
            return day
    raise NotFoundError("Giorno non trovato", f"La scheda non ha il giorno {day_id}.")


def _slot(plan: Plan, slot_id: int) -> tuple[PlanSlot, PlanDay]:
    for day in plan.days:
        for slot in day.slots:
            if slot.id == slot_id:
                return slot, day
    raise NotFoundError("Slot non trovato", f"La scheda non ha lo slot {slot_id}.")


def _family(session: Session, family_id: int) -> MovementFamily:
    family = session.get(MovementFamily, family_id)
    if family is None:
        raise RuleViolationError(
            (RuleError("unknown-reference", "family_id", "La famiglia indicata non esiste."),)
        )
    return family


def _exercise_codes(session: Session) -> dict[int, str]:
    rows: dict[int, str] = dict(session.execute(select(Exercise.id, Exercise.code)).all())
    return rows


def _kind(catalog: Catalog, code: str | None) -> Kind | None:
    exercise = catalog.exercises.get(code) if code else None
    return exercise.kind if exercise else None


def _best(session: Session, plan: Plan, catalog: Catalog, family: str) -> int | None:
    """Il miglior candidato della famiglia con le preferenze della scheda (§ 3)."""
    prefs = plan_preferences(plan.preferences, equipment_order(session))
    best = best_candidate(family, catalog, prefs.scoring, load_score_weights(session))
    if best is None:
        return None
    exercise_id: int | None = session.scalar(
        select(Exercise.id).where(Exercise.code == best.exercise)
    )
    return exercise_id


def _check(
    slot: PlanSlot,
    day: PlanDay,
    family: str,
    catalog: Catalog,
    codes: Mapping[int, str],
    changed: set[str],
) -> None:
    """Regole del dominio sullo slot come sarebbe dopo la modifica."""

    def code(exercise_id: int | None) -> str | None:
        # Un id inesistente diventa un codice che il catalogo non conosce:
        # il dominio lo segnala come riferimento sconosciuto.
        return None if exercise_id is None else codes.get(exercise_id, f"#{exercise_id}")

    violations = check_slot(
        SlotState(
            family=family,
            exercise=code(slot.exercise_id),
            second_exercise=code(slot.second_exercise_id),
            times_per_week=day.times_per_week,
            rep_min=slot.rep_min,
            rep_max=slot.rep_max,
        ),
        catalog,
        changed,
    )
    if violations:
        raise RuleViolationError(tuple(RuleError(v.rule, v.field, v.message) for v in violations))


def _index(position: int | None, length: int) -> int:
    """Posizione richiesta (da 1) come indice di inserimento; senza, in fondo."""
    if position is None:
        return length
    return min(max(position, 1), length + 1) - 1


def _in_order[T: (PlanDay, PlanSlot)](
    items: Sequence[T], ids: Sequence[int], field: str
) -> list[T]:
    by_id = {item.id: item for item in items}
    if sorted(ids) != sorted(by_id):
        raise RuleViolationError(
            (
                RuleError(
                    "order-mismatch",
                    field,
                    "L'ordine deve elencare tutti gli elementi, ciascuno una volta.",
                ),
            )
        )
    return [by_id[item_id] for item_id in ids]


def _renumber(session: Session, items: Sequence[PlanDay | PlanSlot]) -> None:
    """Posizioni 1, 2, 3… nell'ordine dato.

    Passando prima per valori negativi il vincolo di unicità sulle posizioni non
    scatta a metà dell'aggiornamento (modello dati, § 4.6).
    """
    for index, item in enumerate(items, 1):
        item.position = TEMPORARY_OFFSET - index
    session.flush()
    for index, item in enumerate(items, 1):
        item.position = index
    session.flush()
