"""Volume settimanale frazionario e valori effettivi (algoritmo, § 2)."""

from collections.abc import Mapping
from dataclasses import dataclass

from gym_split_planner.domain.enums import BandStatus, Priority
from gym_split_planner.domain.model import (
    Catalog,
    Day,
    LevelWeights,
    MuscleTarget,
    Overrides,
    PlanShape,
    Slot,
    TagRule,
)


def resolve_muscle(target: MuscleTarget, overrides: Overrides) -> MuscleTarget:
    """Priorità e fascia effettive: personalizzazione della scheda, altrimenti catalogo."""
    override = overrides.muscles.get(target.code)
    if override is None:
        return target
    priority = override.priority or target.priority
    if priority is Priority.NONE:
        return MuscleTarget(target.code, priority)
    return MuscleTarget(
        target.code,
        priority,
        override.weekly_min if override.weekly_min is not None else target.weekly_min,
        override.weekly_max if override.weekly_max is not None else target.weekly_max,
    )


def resolve_tag(rule: TagRule, overrides: Overrides) -> TagRule:
    """Effetto e punti effettivi di un'etichetta."""
    override = overrides.tags.get(rule.code)
    if override is None:
        return rule
    return TagRule(
        rule.code,
        override.effect or rule.effect,
        override.points if override.points is not None else rule.points,
    )


def band_status(volume: float, target: MuscleTarget) -> BandStatus | None:
    """Stato rispetto alla fascia; ``None`` per i muscoli senza obiettivo."""
    if target.priority is Priority.NONE or target.weekly_min is None or target.weekly_max is None:
        return None
    if volume < target.weekly_min:
        return BandStatus.BELOW
    if volume > target.weekly_max:
        return BandStatus.ABOVE
    return BandStatus.WITHIN


def _add(
    totals: dict[str, float], catalog: Catalog, exercise: str, sets: float, weights: LevelWeights
) -> None:
    for muscle, level in catalog.exercises[exercise].muscles.items():
        totals[muscle] = totals.get(muscle, 0.0) + sets * weights.of(level)


def counts(slot: Slot) -> bool:
    """Uno slot entra nel volume se non è facoltativo e ha un esercizio."""
    return not slot.optional and slot.exercise is not None


def weekly_volume(
    plan: PlanShape, catalog: Catalog, weights: LevelWeights | None = None
) -> dict[str, float]:
    """Serie frazionarie a settimana per ogni muscolo del catalogo (§ 2.1).

    La variante della seconda seduta sostituisce l'esercizio principale in una delle
    ``t`` sedute settimanali del giorno.
    """
    weights = weights or LevelWeights()
    totals = dict.fromkeys(catalog.muscles, 0.0)
    for day in plan.days:
        for slot in day.slots:
            if not counts(slot):
                continue
            assert slot.exercise is not None
            per_session = slot.sets * slot.weekly_weight
            if slot.second_exercise is not None and day.times_per_week >= 2:
                _add(
                    totals, catalog, slot.exercise, per_session * (day.times_per_week - 1), weights
                )
                _add(totals, catalog, slot.second_exercise, per_session, weights)
            else:
                _add(totals, catalog, slot.exercise, per_session * day.times_per_week, weights)
    return totals


def session_exercises(day: Day) -> list[list[tuple[Slot, str]]]:
    """Sedute concrete del giorno (§ 2.3): una, o due se c'è almeno una variante
    della seconda seduta e il giorno si ripete. Solo gli slot che contano."""
    first = [(slot, slot.exercise) for slot in day.slots if counts(slot) and slot.exercise]
    has_second = day.times_per_week >= 2 and any(
        counts(slot) and slot.second_exercise for slot in day.slots
    )
    if not has_second:
        return [first]
    second = [(slot, slot.second_exercise or exercise) for slot, exercise in first]
    return [first, second]


def session_volumes(
    day: Day, catalog: Catalog, weights: LevelWeights | None = None
) -> list[dict[str, float]]:
    """Volume di ogni seduta concreta del giorno, per muscolo."""
    weights = weights or LevelWeights()
    result = []
    for session in session_exercises(day):
        totals: dict[str, float] = {}
        for slot, exercise in session:
            _add(totals, catalog, exercise, slot.sets * slot.weekly_weight, weights)
        result.append(totals)
    return result


@dataclass(frozen=True)
class SessionCapExcess:
    """Muscolo oltre il tetto in una seduta (avviso ``session-cap``)."""

    day: str
    session: int
    muscle: str
    volume: float


def session_cap_excesses(
    plan: PlanShape, catalog: Catalog, cap: float, weights: LevelWeights | None = None
) -> list[SessionCapExcess]:
    """Tutti i muscoli che superano ``cap`` serie frazionarie in una seduta."""
    excesses: list[SessionCapExcess] = []
    for day in plan.days:
        for index, volumes in enumerate(session_volumes(day, catalog, weights), 1):
            excesses.extend(
                SessionCapExcess(day.code, index, muscle, volume)
                for muscle, volume in sorted(volumes.items())
                if volume > cap
            )
    return excesses


def effective_targets(catalog: Catalog, overrides: Overrides) -> Mapping[str, MuscleTarget]:
    """Valori effettivi di tutti i muscoli; le personalizzazioni di muscoli assenti si ignorano."""
    return {code: resolve_muscle(target, overrides) for code, target in catalog.muscles.items()}
