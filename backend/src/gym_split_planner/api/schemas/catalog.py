"""Schemi del catalogo in lettura (API, § 6.2).

I valori enumerati sono gli stessi del database (API, § 2), dichiarati come
``Literal`` perché lo strato api non importa il dominio (ADR 0005): lo schema
OpenAPI li elenca e il client li riceve come tipi unione.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from gym_split_planner.api.schemas.inputs import HttpUrl, Label, LongText, Name, ShortText

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


# --- Scrittura (API, § 6.3) -------------------------------------------------------


class MuscleLinkIn(BaseModel):
    """Muscolo coinvolto nell'esercizio."""

    muscle_id: int
    level: Level
    note: ShortText = None


class TagLinkIn(BaseModel):
    """Etichetta assegnata, con nota facoltativa."""

    tag_id: int
    note: ShortText = None


class ExerciseIn(BaseModel):
    """Esercizio completo: la form invia sempre tutti i campi (US-03).

    Almeno un muscolo P, famiglia secondaria diversa dalla principale, nome libero:
    altrimenti ``422 rule-violation`` con l'elenco ``violations``.
    """

    name: Name
    primary_family_id: int
    secondary_family_id: int | None = None
    family_rank: int = Field(default=1, ge=1, le=999)
    equipment_id: int
    equipment_detail: ShortText = None
    kind: Kind
    stretch: Stretch
    stretch_note: ShortText = None
    confidence: Confidence
    notes: LongText = None
    is_active: bool = True
    muscles: list[MuscleLinkIn] = Field(max_length=100)
    tags: list[TagLinkIn] = Field(default_factory=list, max_length=50)
    source_ids: list[int] = Field(default_factory=list, max_length=100)


class ExerciseCreateIn(ExerciseIn):
    """Come ``ExerciseIn``, con il ``code`` facoltativo: senza, si genera dal nome."""

    code: str | None = None


class PlanUsageOut(_Out):
    """Scheda che usa una risorsa, con quanti slot."""

    id: int
    name: str
    slots: int


class ExerciseUsageOut(_Out):
    """Dove è usato un esercizio: serve alla conferma di eliminazione."""

    plans: list[PlanUsageOut]


class SourceIn(BaseModel):
    """Nuova fonte. Il codice è il successivo della serie ``src-NN``."""

    title: Name
    kind: Label
    url: HttpUrl = None
    reliability: ShortText = None
    used_for: LongText = None


class SourcePatch(BaseModel):
    """Modifica parziale di una fonte: cambiano solo i campi inviati."""

    title: Name | None = None
    kind: Label | None = None
    url: HttpUrl = None
    reliability: ShortText = None
    used_for: LongText = None

    @field_validator("title", "kind")
    @classmethod
    def _not_null(cls, value: str | None) -> str:
        """Titolo e tipo si possono omettere, non svuotare."""
        if value is None:
            raise ValueError("Il campo non può essere vuoto")
        return value
