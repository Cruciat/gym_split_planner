"""Anteprima delle varianti: effetto sul volume di ogni candidato (algoritmo, § 5)."""

from dataclasses import dataclass

from gym_split_planner.domain.model import Catalog, Day, LevelWeights, Slot
from gym_split_planner.domain.scoring import (
    Candidate,
    Preferences,
    ScoreWeights,
    candidates,
    score_exercise,
)


@dataclass(frozen=True)
class VariantPreview:
    """Un candidato con i muscoli il cui volume settimanale cambierebbe."""

    candidate: Candidate
    volume_delta: dict[str, float]


def _delta(
    catalog: Catalog,
    new: str,
    current: str | None,
    sets: float,
    weights: LevelWeights,
) -> dict[str, float]:
    new_muscles = catalog.exercises[new].muscles
    old_muscles = catalog.exercises[current].muscles if current else {}
    result = {}
    for muscle in sorted(set(new_muscles) | set(old_muscles)):
        change = sets * (weights.of(new_muscles.get(muscle)) - weights.of(old_muscles.get(muscle)))
        if change:
            result[muscle] = change
    return result


def slot_occurrences(day: Day, slot: Slot) -> int:
    """Sedute settimanali in cui si usa l'esercizio principale dello slot.

    ``t`` volte a settimana, oppure ``t - 1`` se c'è una variante della seconda seduta.
    """
    has_second = slot.second_exercise is not None and day.times_per_week >= 2
    return day.times_per_week - 1 if has_second else day.times_per_week


def main_exercise_delta(
    day: Day,
    position: int,
    new: str,
    catalog: Catalog,
    level_weights: LevelWeights | None = None,
) -> dict[str, float]:
    """Effetto sul volume settimanale di cambiare l'esercizio principale dello slot.

    È la stessa formula dell'anteprima delle varianti (§ 5); serve anche alle
    differenze della rigenerazione (§ 4.2). Uno slot facoltativo non cambia nulla.
    """
    slot = day.slots[position - 1]
    if slot.optional:
        return {}
    sets = slot.sets * slot.weekly_weight * slot_occurrences(day, slot)
    return _delta(catalog, new, slot.exercise, sets, level_weights or LevelWeights())


def variant_previews(
    day: Day,
    position: int,
    catalog: Catalog,
    preferences: Preferences,
    *,
    session: int = 1,
    score_weights: ScoreWeights | None = None,
    level_weights: LevelWeights | None = None,
) -> list[VariantPreview]:
    """Candidati per lo slot ``position`` (da 1) del giorno, con l'effetto sul volume.

    - ``session=1``: esercizio principale, candidati della famiglia dello slot; conta
      per le sedute in cui il principale si usa (``t``, o ``t - 1`` con la seconda seduta).
    - ``session=2``: variante della seconda seduta, prima la famiglia dello slot, poi
      tutti gli altri esercizi attivi; conta per una seduta, rispetto all'esercizio
      usato oggi in quella seduta.

    Uno slot facoltativo non entra nel volume: le differenze sono vuote.
    """
    score_weights = score_weights or ScoreWeights()
    level_weights = level_weights or LevelWeights()
    slot = day.slots[position - 1]
    found = candidates(slot.family, catalog, preferences, score_weights)
    if session == 2:
        same_family = {c.exercise for c in found}
        others = [
            score_exercise(e, 0.0, catalog, preferences, score_weights)
            for e in catalog.exercises.values()
            if e.is_active and e.code not in same_family
        ]
        found += sorted(others, key=lambda c: (c.excluded, -round(c.score, 9), c.exercise))
        occurrences = 1
        current = slot.second_exercise or slot.exercise
    else:
        occurrences = slot_occurrences(day, slot)
        current = slot.exercise
    sets = 0.0 if slot.optional else slot.sets * slot.weekly_weight * occurrences
    return [
        VariantPreview(c, _delta(catalog, c.exercise, current, sets, level_weights) if sets else {})
        for c in found
    ]
