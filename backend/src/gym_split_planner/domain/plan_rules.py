"""Regole di giorni e slot di una scheda (modello dati, § 7; API, § 6.8).

Le regole che attraversano più tabelle (l'esercizio appartiene alla famiglia dello
slot, la variante della seconda seduta esiste solo nei giorni ripetuti) vivono qui,
come funzioni pure; il servizio le applica allo stato dello slot *dopo* la modifica
richiesta, così una modifica si accetta o si rifiuta per intero.
"""

from collections.abc import Set
from dataclasses import dataclass

from gym_split_planner.domain.catalog_rules import Violation
from gym_split_planner.domain.enums import Kind
from gym_split_planner.domain.model import Catalog

DEFAULT_PRESCRIPTION = {
    Kind.COMPOUND: (3, 6, 12),
    Kind.ISOLATION: (3, 10, 15),
}
"""Serie e ripetizioni di uno slot aggiunto a mano senza indicarle (API, § 11.1)."""


@dataclass(frozen=True)
class SlotState:
    """Lo slot come sarebbe dopo la modifica, con i ``code`` degli esercizi."""

    family: str
    exercise: str | None
    second_exercise: str | None
    times_per_week: int
    rep_min: int
    rep_max: int


def default_prescription(kind: Kind | None) -> tuple[int, int, int]:
    """Serie, ripetizioni minime e massime per tipo; senza esercizio, come un multiarticolare."""
    return DEFAULT_PRESCRIPTION[kind or Kind.COMPOUND]


def check_slot(
    state: SlotState, catalog: Catalog, changed: Set[str] = frozenset({"exercise"})
) -> tuple[Violation, ...]:
    """Tutte le regole violate dallo slot.

    - L'esercizio deve avere la famiglia dello slot come principale o secondaria.
    - Un esercizio disattivato non si sceglie (ma resta dove già era): la regola vale
      solo se ``"exercise"`` o ``"second_exercise"`` sono tra i campi cambiati.
    - La variante della seconda seduta richiede un giorno ripetuto almeno 2 volte, è
      diversa dall'esercizio principale e può essere di qualunque famiglia.
    - Ripetizioni minime non oltre le massime.
    """
    violations: list[Violation] = []

    exercise = catalog.exercises.get(state.exercise) if state.exercise else None
    if state.exercise is not None and exercise is None:
        violations.append(_unknown("exercise_id"))
    elif exercise is not None:
        if exercise.family_match(state.family) is None:
            violations.append(
                Violation(
                    "exercise-family",
                    "exercise_id",
                    "L'esercizio non appartiene alla famiglia dello slot.",
                )
            )
        if "exercise" in changed and not exercise.is_active:
            violations.append(_inactive("exercise_id"))

    if state.second_exercise is not None:
        second = catalog.exercises.get(state.second_exercise)
        if second is None:
            violations.append(_unknown("second_exercise_id"))
        elif state.times_per_week < 2:
            violations.append(
                Violation(
                    "second-session-requires-repeat",
                    "second_exercise_id",
                    "La variante della seconda seduta serve solo nei giorni ripetuti "
                    "almeno due volte a settimana.",
                )
            )
        elif state.second_exercise == state.exercise:
            violations.append(
                Violation(
                    "second-exercise-distinct",
                    "second_exercise_id",
                    "La variante della seconda seduta deve essere diversa dall'esercizio "
                    "principale.",
                )
            )
        elif "second_exercise" in changed and not second.is_active:
            violations.append(_inactive("second_exercise_id"))

    if state.rep_min > state.rep_max:
        violations.append(
            Violation(
                "reps-order",
                "rep_max",
                "Le ripetizioni massime non possono essere meno delle minime.",
            )
        )
    return tuple(violations)


def _unknown(field: str) -> Violation:
    return Violation("unknown-reference", field, "L'esercizio indicato non esiste.")


def _inactive(field: str) -> Violation:
    return Violation(
        "exercise-inactive",
        field,
        "L'esercizio è disattivato: riattivalo nel catalogo per sceglierlo.",
    )
