"""Stima della durata di una seduta (algoritmo, § 6)."""

from dataclasses import dataclass

from gym_split_planner.domain.enums import Kind
from gym_split_planner.domain.model import Catalog, Day, Slot
from gym_split_planner.domain.volume import session_exercises


@dataclass(frozen=True)
class DurationParams:
    """Parametri della stima (``app_setting.duration_params``)."""

    set_seconds: float = 45
    rest_compound_seconds: float = 150
    rest_isolation_seconds: float = 90
    change_seconds: float = 60
    warmup_set_seconds: float = 30
    warmup_rest_seconds: float = 60
    warmup_minutes: float = 10
    stretching_minutes: float = 6


def rest_seconds(kind: Kind, params: DurationParams) -> float:
    """Recupero tra le serie allenanti: più lungo per i multiarticolari."""
    return params.rest_compound_seconds if kind is Kind.COMPOUND else params.rest_isolation_seconds


def session_minutes(
    session: list[tuple[Slot, str]], catalog: Catalog, params: DurationParams
) -> float:
    """Durata di una seduta concreta, in minuti.

    Due serie di avvicinamento per ogni gruppo muscolare il cui primo esercizio nella
    seduta è multiarticolare: è la regola del documento (avvicinamento sul primo
    esercizio di ogni muscolo).
    """
    seconds = (params.warmup_minutes + params.stretching_minutes) * 60
    seen_groups: set[str] = set()
    for slot, code in session:
        exercise = catalog.exercises[code]
        rest = rest_seconds(exercise.kind, params)
        seconds += slot.weekly_weight * (
            slot.sets * params.set_seconds + (slot.sets - 1) * rest + params.change_seconds
        )
        if exercise.group not in seen_groups:
            seen_groups.add(exercise.group)
            if exercise.kind is Kind.COMPOUND:
                seconds += 2 * (params.warmup_set_seconds + params.warmup_rest_seconds)
    return seconds / 60


def day_minutes(day: Day, catalog: Catalog, params: DurationParams | None = None) -> list[float]:
    """Durata di ogni seduta concreta del giorno (una, o due con la seconda seduta)."""
    params = params or DurationParams()
    return [session_minutes(s, catalog, params) for s in session_exercises(day)]
