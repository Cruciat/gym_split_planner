"""Candidati di uno slot e loro punteggio (algoritmo, § 3)."""

from collections.abc import Mapping
from dataclasses import dataclass, field

from gym_split_planner.domain.enums import Confidence, Stretch, TagEffect
from gym_split_planner.domain.model import Catalog, ExerciseInfo, Overrides
from gym_split_planner.domain.volume import resolve_tag

CONFIDENCE_VALUE: Mapping[Confidence, float] = {
    Confidence.SOLID: 1.0,
    Confidence.LIMITED: 0.6,
    Confidence.OPINION: 0.3,
}
STRETCH_VALUE: Mapping[Stretch, float] = {
    Stretch.HIGH: 1.0,
    Stretch.MEDIUM: 0.6,
    Stretch.LOW: 0.2,
}
DEFAULT_EQUIPMENT_ORDER = ("machine", "cable", "free-weight", "bodyweight")


@dataclass(frozen=True)
class ScoreWeights:
    """Pesi della base del punteggio (``app_setting.score_weights``)."""

    confidence: float = 3.0
    equipment: float = 4.0
    stretch: float = 1.0
    family: float = 1.0
    rank: float = 0.5


@dataclass(frozen=True)
class Preferences:
    """Preferenze della scheda che influiscono sulla scelta degli esercizi."""

    equipment_order: tuple[str, ...] = DEFAULT_EQUIPMENT_ORDER
    overrides: Overrides = field(default_factory=Overrides)


@dataclass(frozen=True)
class ScoreBreakdown:
    """Voci del punteggio, già moltiplicate per i pesi: la somma è il punteggio."""

    confidence: float
    equipment: float
    stretch: float
    family: float
    rank: float
    tags: float

    @property
    def total(self) -> float:
        return self.confidence + self.equipment + self.stretch + self.family + self.rank + self.tags


@dataclass(frozen=True)
class Candidate:
    """Esercizio candidato per una famiglia, con punteggio ed eventuali esclusioni."""

    exercise: str
    family_match: float
    breakdown: ScoreBreakdown
    excluded_by: tuple[str, ...] = ()

    @property
    def score(self) -> float:
        return self.breakdown.total

    @property
    def excluded(self) -> bool:
        return bool(self.excluded_by)


def equipment_value(equipment: str, order: tuple[str, ...]) -> float:
    """1 per il primo attrezzo dell'ordine, 0 per l'ultimo, lineare in mezzo; 0 se assente."""
    if equipment not in order:
        return 0.0
    if len(order) == 1:
        return 1.0
    return (len(order) - 1 - order.index(equipment)) / (len(order) - 1)


def score_exercise(
    exercise: ExerciseInfo,
    family_match: float,
    catalog: Catalog,
    preferences: Preferences,
    weights: ScoreWeights,
) -> Candidate:
    """Punteggio di un esercizio per uno slot di una famiglia (§ 3.2)."""
    tags = 0.0
    excluded_by = []
    for code in sorted(exercise.tags):
        rule = catalog.tags.get(code)
        if rule is None:
            continue
        rule = resolve_tag(rule, preferences.overrides)
        if rule.effect is TagEffect.EXCLUDE:
            excluded_by.append(code)
        elif rule.effect is TagEffect.BONUS:
            tags += rule.points
        elif rule.effect is TagEffect.PENALTY:
            tags -= rule.points
    breakdown = ScoreBreakdown(
        confidence=weights.confidence * CONFIDENCE_VALUE[exercise.confidence],
        equipment=weights.equipment
        * equipment_value(exercise.equipment, preferences.equipment_order),
        stretch=weights.stretch * STRETCH_VALUE[exercise.stretch],
        family=weights.family * family_match,
        rank=weights.rank / exercise.family_rank,
        tags=tags,
    )
    return Candidate(exercise.code, family_match, breakdown, tuple(excluded_by))


def candidates(
    family: str,
    catalog: Catalog,
    preferences: Preferences,
    weights: ScoreWeights | None = None,
) -> list[Candidate]:
    """Esercizi attivi della famiglia (principale o secondaria), ordinati (§ 3.3).

    Prima i non esclusi, poi gli esclusi; ciascun gruppo per punteggio decrescente,
    poi ``family_rank`` crescente, poi ``code``. Stessi dati, stesso ordine.
    """
    weights = weights or ScoreWeights()
    found = []
    for exercise in catalog.exercises.values():
        match = exercise.family_match(family)
        if match is None or not exercise.is_active:
            continue
        found.append(score_exercise(exercise, match, catalog, preferences, weights))
    return sorted(
        found,
        key=lambda c: (
            c.excluded,
            -round(c.score, 9),
            catalog.exercises[c.exercise].family_rank,
            c.exercise,
        ),
    )


def best_candidate(
    family: str,
    catalog: Catalog,
    preferences: Preferences,
    weights: ScoreWeights | None = None,
) -> Candidate | None:
    """Il primo candidato non escluso, ``None`` se non ce n'è."""
    for candidate in candidates(family, catalog, preferences, weights):
        if not candidate.excluded:
            return candidate
    return None
