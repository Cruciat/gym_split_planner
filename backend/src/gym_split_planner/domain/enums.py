"""Valori enumerati del dominio (modello dati, ADR 0013).

I valori sono stringhe in inglese, salvate così come sono nel database (con un
vincolo ``CHECK``) e usate nel JSON dell'API.
"""

from enum import StrEnum


class Priority(StrEnum):
    """Priorità di un muscolo: decide se ha una fascia obiettivo."""

    PRIORITY = "priority"
    """Prioritario."""
    STANDARD = "standard"
    """Non prioritario, ma con una fascia."""
    NONE = "none"
    """Nessun obiettivo: il volume si mostra senza giudizio."""


class Level(StrEnum):
    """Coinvolgimento di un muscolo in un esercizio."""

    PRIMARY = "P"
    SECONDARY = "S"


class Kind(StrEnum):
    """Tipo di esercizio."""

    COMPOUND = "compound"
    ISOLATION = "isolation"


class Stretch(StrEnum):
    """Allungamento del muscolo durante l'esercizio."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Confidence(StrEnum):
    """Confidenza delle fonti."""

    SOLID = "solid"
    LIMITED = "limited"
    OPINION = "opinion"


class TagEffect(StrEnum):
    """Effetto di un'etichetta sul punteggio (ADR 0014)."""

    NONE = "none"
    BONUS = "bonus"
    PENALTY = "penalty"
    EXCLUDE = "exclude"


class TagColor(StrEnum):
    """Colore semantico di un'etichetta, tradotto in tinte dal tema."""

    NEUTRAL = "neutral"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"


class RoutineBlock(StrEnum):
    """Blocco del mini-allenamento quotidiano."""

    NECK = "neck"
    PELVIS = "pelvis"
