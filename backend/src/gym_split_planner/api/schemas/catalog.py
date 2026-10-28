"""Schemi del catalogo in lettura (API, § 6.2).

I valori enumerati sono gli stessi del database (API, § 2), dichiarati come
``Literal`` perché lo strato api non importa il dominio (ADR 0005): lo schema
OpenAPI li elenca e il client li riceve come tipi unione.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from gym_split_planner.api.schemas.inputs import (
    HttpUrl,
    Label,
    LongText,
    Name,
    ShortLabel,
    ShortText,
    reject_null,
)

Priority = Literal["priority", "standard", "none"]
Level = Literal["P", "S"]
Kind = Literal["compound", "isolation"]
Stretch = Literal["high", "medium", "low"]
Confidence = Literal["solid", "limited", "opinion"]
TagEffect = Literal["none", "bonus", "penalty", "exclude"]
TagColor = Literal["neutral", "info", "success", "warning", "danger"]
RoutineBlock = Literal["neck", "pelvis"]
TagSymbol = Literal["warning", "ban", "info", "star", "heart", "zap", "flag", "eye-off"]
"""Insieme chiuso dei simboli delle etichette (wireframe, § 4.4): icone di Lucide."""


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

    _not_null = field_validator("title", "kind")(reject_null)


class PlanRefOut(_Out):
    """Scheda citata da un utilizzo o da un errore."""

    id: int
    name: str


# --- Famiglie (US-06) ------------------------------------------------------------


class FamilyIn(BaseModel):
    """Nuova famiglia di movimento. Senza ``code``, si genera dal nome."""

    name: Label
    description: LongText = None
    muscle_group_id: int
    code: str | None = None


class FamilyPatch(BaseModel):
    """Modifica parziale di una famiglia; il ``code`` non cambia."""

    name: Label | None = None
    description: LongText = None
    muscle_group_id: int | None = None
    sort_order: int | None = Field(default=None, ge=1)

    _not_null = field_validator("name", "muscle_group_id", "sort_order")(reject_null)


class FamilyUsageOut(_Out):
    """Chi usa una famiglia. Esercizi principali, slot e schede ne impediscono l'eliminazione."""

    exercises: int
    secondary_exercises: int
    split_slots: int
    plans: list[PlanUsageOut]


# --- Muscoli (US-07) -------------------------------------------------------------


class MusclePatch(BaseModel):
    """Modifica parziale di un muscolo. Con ``priority: "none"`` la fascia si svuota;
    altrimenti servono minimo e massimo, con minimo < massimo."""

    name: Label | None = None
    short_name: ShortLabel | None = None
    priority: Priority | None = None
    weekly_min: float | None = Field(default=None, le=100)
    weekly_max: float | None = Field(default=None, le=100)
    notes: LongText = None

    _not_null = field_validator("name", "short_name", "priority")(reject_null)


# --- Etichette (US-08) -----------------------------------------------------------


class TagIn(BaseModel):
    """Nuova etichetta. Bonus e penalità hanno bisogno di punti maggiori di zero."""

    name: Label
    description: LongText = None
    symbol: TagSymbol
    color: TagColor = "neutral"
    effect: TagEffect = "none"
    points: float = Field(default=0, ge=0, le=100)
    show_badge: bool = True
    code: str | None = None


class TagPatch(BaseModel):
    """Modifica parziale di un'etichetta."""

    name: Label | None = None
    description: LongText = None
    symbol: TagSymbol | None = None
    color: TagColor | None = None
    effect: TagEffect | None = None
    points: float | None = Field(default=None, ge=0, le=100)
    show_badge: bool | None = None
    sort_order: int | None = Field(default=None, ge=1)

    _not_null = field_validator(
        "name", "symbol", "color", "effect", "points", "show_badge", "sort_order"
    )(reject_null)


class TagUsageOut(_Out):
    """Esercizi con l'etichetta e schede che la personalizzano."""

    exercises: int
    plans_with_overrides: list[PlanRefOut]


class TagAssignIn(BaseModel):
    """Esercizi a cui assegnare l'etichetta. La nota vale per tutti: a chi ha già
    l'etichetta si aggiorna solo se il campo ``note`` è presente."""

    exercise_ids: list[int] = Field(min_length=1, max_length=1000)
    note: ShortText = None


class TagUnassignIn(BaseModel):
    """Esercizi da cui togliere l'etichetta."""

    exercise_ids: list[int] = Field(min_length=1, max_length=1000)
