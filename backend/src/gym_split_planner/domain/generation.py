"""Generazione e rigenerazione delle schede (algoritmo, § 4)."""

from dataclasses import dataclass, replace

from gym_split_planner.domain.model import Catalog, Day, PlanShape
from gym_split_planner.domain.scoring import (
    Preferences,
    ScoreWeights,
    best_candidate,
    candidates,
)


@dataclass(frozen=True)
class EmptySlot:
    """Slot senza candidati validi (avviso ``empty-slot``)."""

    day: str
    position: int
    """Posizione nel giorno, da 1."""
    family: str
    excluded_by: tuple[str, ...]
    """Etichette che escludono gli esercizi della famiglia; vuoto se la famiglia non ne ha."""


@dataclass(frozen=True)
class SlotChange:
    """Differenza proposta dalla rigenerazione per uno slot."""

    day: str
    position: int
    current: str | None
    proposed: str


def _empty_reason(
    day: str, position: int, family: str, catalog: Catalog, preferences: Preferences
) -> EmptySlot:
    reasons = sorted(
        {code for c in candidates(family, catalog, preferences) for code in c.excluded_by}
    )
    return EmptySlot(day, position, family, tuple(reasons))


def generate(
    shape: PlanShape,
    catalog: Catalog,
    preferences: Preferences,
    weights: ScoreWeights | None = None,
) -> tuple[PlanShape, list[EmptySlot]]:
    """Assegna a ogni slot il miglior candidato della sua famiglia (§ 4.1).

    Serie, ripetizioni, facoltativo e peso restano quelli dello split. La variante
    della seconda seduta resta vuota e i lucchetti aperti.
    """
    days = []
    empty = []
    for day in shape.days:
        slots = []
        for position, slot in enumerate(day.slots, 1):
            best = best_candidate(slot.family, catalog, preferences, weights)
            if best is None:
                empty.append(_empty_reason(day.code, position, slot.family, catalog, preferences))
            slots.append(
                replace(
                    slot,
                    exercise=best.exercise if best else None,
                    second_exercise=None,
                    locked=False,
                )
            )
        days.append(Day(day.code, day.times_per_week, tuple(slots)))
    return PlanShape(tuple(days)), empty


def regeneration_changes(
    plan: PlanShape,
    catalog: Catalog,
    preferences: Preferences,
    weights: ScoreWeights | None = None,
) -> list[SlotChange]:
    """Differenze tra la scheda e una nuova generazione (§ 4.2).

    Gli slot bloccati non cambiano. Uno slot senza candidati validi resta com'è.
    Serie e ripetizioni non fanno parte delle differenze: si mantengono sempre.
    """
    changes = []
    for day in plan.days:
        for position, slot in enumerate(day.slots, 1):
            if slot.locked:
                continue
            best = best_candidate(slot.family, catalog, preferences, weights)
            if best is not None and best.exercise != slot.exercise:
                changes.append(SlotChange(day.code, position, slot.exercise, best.exercise))
    return changes


def apply_changes(plan: PlanShape, changes: list[SlotChange]) -> PlanShape:
    """Applica le differenze scelte; cambia solo l'esercizio principale degli slot indicati."""
    proposed = {(c.day, c.position): c.proposed for c in changes}
    days = []
    for day in plan.days:
        slots = tuple(
            replace(slot, exercise=proposed.get((day.code, position), slot.exercise))
            for position, slot in enumerate(day.slots, 1)
        )
        days.append(Day(day.code, day.times_per_week, slots))
    return PlanShape(tuple(days))
