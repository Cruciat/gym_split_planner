"""Oggetti del dominio: catalogo, personalizzazioni e forma della scheda (algoritmo, § 1).

Strutture immutabili e indipendenti dal database. Gli esercizi, i muscoli e le
etichette si identificano con il loro ``code``, stabile tra installazioni.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from gym_split_planner.domain.enums import (
    Confidence,
    Kind,
    Level,
    Priority,
    Stretch,
    TagEffect,
)


def _frozen[K, V](mapping: Mapping[K, V] | None = None) -> Mapping[K, V]:
    return MappingProxyType(dict(mapping or {}))


# --- Catalogo -----------------------------------------------------------------------


@dataclass(frozen=True)
class MuscleTarget:
    """Priorità e fascia obiettivo di un muscolo (del catalogo o effettive)."""

    code: str
    priority: Priority
    weekly_min: float | None = None
    weekly_max: float | None = None


@dataclass(frozen=True)
class TagRule:
    """Effetto di un'etichetta sul punteggio (del catalogo o effettivo)."""

    code: str
    effect: TagEffect
    points: float = 0.0


@dataclass(frozen=True)
class ExerciseInfo:
    """Ciò che serve ai calcoli di un esercizio del catalogo."""

    code: str
    primary_family: str
    family_rank: int
    equipment: str
    kind: Kind
    stretch: Stretch
    confidence: Confidence
    muscles: Mapping[str, Level]
    secondary_family: str | None = None
    tags: frozenset[str] = frozenset()
    is_active: bool = True

    def family_match(self, family: str) -> float | None:
        """1 se ``family`` è la principale, 0,5 se è la secondaria, ``None`` altrimenti."""
        if family == self.primary_family:
            return 1.0
        if family == self.secondary_family:
            return 0.5
        return None


@dataclass(frozen=True)
class Catalog:
    """Catalogo in memoria, con indici per ``code``."""

    exercises: Mapping[str, ExerciseInfo]
    muscles: Mapping[str, MuscleTarget]
    tags: Mapping[str, TagRule] = field(default_factory=_frozen)

    @staticmethod
    def build(
        exercises: list[ExerciseInfo],
        muscles: list[MuscleTarget],
        tags: list[TagRule] | None = None,
    ) -> "Catalog":
        return Catalog(
            exercises=_frozen({e.code: e for e in exercises}),
            muscles=_frozen({m.code: m for m in muscles}),
            tags=_frozen({t.code: t for t in tags or []}),
        )


# --- Personalizzazioni (ADR 0014, modello dati § 4.7) --------------------------------------


@dataclass(frozen=True)
class MuscleOverride:
    priority: Priority | None = None
    weekly_min: float | None = None
    weekly_max: float | None = None


@dataclass(frozen=True)
class TagOverride:
    effect: TagEffect | None = None
    points: float | None = None


@dataclass(frozen=True)
class Overrides:
    """Differenze della scheda rispetto al catalogo; ciò che manca segue il catalogo."""

    muscles: Mapping[str, MuscleOverride] = field(default_factory=_frozen)
    tags: Mapping[str, TagOverride] = field(default_factory=_frozen)


# --- Forma della scheda ----------------------------------------------------------------


@dataclass(frozen=True)
class Slot:
    """Posto di un giorno: famiglia, esercizio scelto ed eventuale seconda seduta."""

    family: str
    sets: int
    rep_min: int
    rep_max: int
    exercise: str | None = None
    second_exercise: str | None = None
    optional: bool = False
    weekly_weight: float = 1.0
    locked: bool = False


@dataclass(frozen=True)
class Day:
    """Giorno ripetuto ``times_per_week`` volte (1-3) a settimana."""

    code: str
    times_per_week: int
    slots: tuple[Slot, ...]


@dataclass(frozen=True)
class PlanShape:
    """Giorni e slot di una scheda (o di uno split, con gli esercizi ancora da scegliere)."""

    days: tuple[Day, ...]


@dataclass(frozen=True)
class LevelWeights:
    """Valore del coinvolgimento P e S nel volume frazionario."""

    primary: float = 1.0
    secondary: float = 0.5

    def of(self, level: Level | None) -> float:
        if level is Level.PRIMARY:
            return self.primary
        if level is Level.SECONDARY:
            return self.secondary
        return 0.0
