"""Schemi del catalogo in lettura (API, § 6.2).

I valori enumerati sono gli stessi del database (API, § 2), dichiarati come
``Literal`` perché lo strato api non importa il dominio (ADR 0005): lo schema
OpenAPI li elenca e il client li riceve come tipi unione.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

Priority = Literal["priority", "standard", "none"]
Level = Literal["P", "S"]
Kind = Literal["compound", "isolation"]
Stretch = Literal["high", "medium", "low"]
Confidence = Literal["solid", "limited", "opinion"]
TagEffect = Literal["none", "bonus", "penalty", "exclude"]
TagColor = Literal["neutral", "info", "success", "warning", "danger"]
RoutineBlock = Literal["neck", "pelvis"]


class _Out(BaseModel):
    """Base delle risposte: si costruiscono dalle dataclass dei servizi."""

    model_config = ConfigDict(from_attributes=True)


class MuscleGroupOut(_Out):
    id: int
    code: str
    name: str
    sort_order: int


class MuscleOut(_Out):
    """Muscolo con priorità e fascia del catalogo."""

    id: int
    code: str
    name: str
    short_name: str
    muscle_group_id: int
    priority: Priority
    weekly_min: float | None
    weekly_max: float | None
    notes: str | None
    sort_order: int


class EquipmentOut(_Out):
    id: int
    code: str
    name: str
    sort_order: int


class FamilyOut(_Out):
    """Famiglia di movimento."""

    id: int
    code: str
    name: str
    description: str | None
    muscle_group_id: int
    sort_order: int


class TagOut(_Out):
    """Etichetta con simbolo ed effetto sul punteggio (ADR 0014)."""

    id: int
    code: str
    name: str
    description: str | None
    symbol: str
    color: TagColor
    effect: TagEffect
    points: float
    show_badge: bool
    sort_order: int


class SourceOut(_Out):
    id: int
    code: str
    title: str
    kind: str
    url: str | None
    reliability: str | None
    used_for: str | None


class StretchOut(_Out):
    id: int
    code: str
    name: str
    targets: str
    instructions: str | None
    dose: str
    confidence: Confidence | None
    note: str | None


class RoutineItemOut(_Out):
    """Voce del mini-allenamento quotidiano."""

    id: int
    block: RoutineBlock
    position: int
    name: str
    dose: str
    purpose: str
    confidence: Confidence


class MuscleLinkOut(_Out):
    """Muscolo coinvolto, con livello P (primario) o S (secondario)."""

    muscle_id: int
    level: Level


class MuscleLinkDetailOut(MuscleLinkOut):
    """Muscolo coinvolto, con la nota (es. "solo con i manubri")."""

    note: str | None


class TagLinkOut(_Out):
    """Etichetta assegnata, con la nota dell'assegnazione."""

    tag_id: int
    note: str | None


class ExerciseSummaryOut(_Out):
    """Riepilogo di un esercizio: basta per la lista e per i filtri (US-01)."""

    id: int
    code: str
    name: str
    primary_family_id: int
    secondary_family_id: int | None
    family_rank: int
    equipment_id: int
    equipment_detail: str | None
    kind: Kind
    stretch: Stretch
    confidence: Confidence
    is_active: bool
    muscles: list[MuscleLinkOut]
    tags: list[TagLinkOut]


class CatalogOut(_Out):
    """Tutto il catalogo in una risposta (API, § 6.2)."""

    muscle_groups: list[MuscleGroupOut]
    muscles: list[MuscleOut]
    equipment: list[EquipmentOut]
    families: list[FamilyOut]
    tags: list[TagOut]
    exercises: list[ExerciseSummaryOut]
    sources: list[SourceOut]
    stretches: list[StretchOut]
    daily_routine: list[RoutineItemOut]


class VariantOut(_Out):
    """Altro esercizio attivo di una delle famiglie dell'esercizio."""

    id: int
    code: str
    name: str
    family_id: int
    equipment_id: int
    family_rank: int
    tags: list[TagLinkOut]


class ExerciseDetailOut(_Out):
    """Dettaglio di un esercizio (US-02)."""

    id: int
    code: str
    name: str
    primary_family_id: int
    secondary_family_id: int | None
    family_rank: int
    equipment_id: int
    equipment_detail: str | None
    kind: Kind
    stretch: Stretch
    stretch_note: str | None
    confidence: Confidence
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    muscles: list[MuscleLinkDetailOut]
    tags: list[TagLinkOut]
    sources: list[SourceOut]
    variants: list[VariantOut]
