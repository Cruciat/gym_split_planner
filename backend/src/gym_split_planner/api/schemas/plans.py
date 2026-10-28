"""Schemi di split e schede (API, § 6.4, § 6.5, § 7)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from gym_split_planner.api.schemas.catalog import Kind, Priority, TagColor, TagEffect
from gym_split_planner.api.schemas.inputs import Label


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Split predefiniti -----------------------------------------------------------


class SplitFamilyOut(_Out):
    id: int
    code: str
    name: str


class SplitSlotOut(_Out):
    family: SplitFamilyOut
    sets: int
    rep_min: int
    rep_max: int
    is_optional: bool
    weekly_weight: float
    note: str | None


class SplitDayOut(_Out):
    name: str
    times_per_week: int
    slots: list[SplitSlotOut]


class SplitOut(_Out):
    """Preset per la procedura guidata (US-10 CA1)."""

    id: int
    code: str
    name: str
    description: str | None
    days_per_week: int
    days: list[SplitDayOut]


# --- Preferenze (modello dati, § 4.7) ---------------------------------------------


class MuscleOverrideIn(BaseModel):
    """Personalizzazione di un muscolo: solo i campi diversi dal catalogo contano."""

    model_config = ConfigDict(extra="forbid")

    priority: Priority | None = None
    weekly_min: float | None = Field(default=None, ge=0, le=100)
    weekly_max: float | None = Field(default=None, ge=0, le=100)


class TagOverrideIn(BaseModel):
    """Personalizzazione di un'etichetta."""

    model_config = ConfigDict(extra="forbid")

    effect: TagEffect | None = None
    points: float | None = Field(default=None, ge=0, le=100)


class OverridesIn(BaseModel):
    """Personalizzazioni per ``code`` di muscolo ed etichetta."""

    model_config = ConfigDict(extra="forbid")

    muscles: dict[str, MuscleOverrideIn] = Field(default_factory=dict)
    tags: dict[str, TagOverrideIn] = Field(default_factory=dict)


class PreferencesIn(BaseModel):
    """Preferenze della scheda. Il server toglie ciò che coincide con il catalogo e i
    codici che non esistono più, poi valida i valori effettivi (``rule-violation``)."""

    model_config = ConfigDict(extra="forbid")

    version: int = 2
    equipment_order: list[str] = Field(min_length=1, max_length=20)
    max_session_minutes: int | None = Field(default=75, ge=15, le=300)
    overrides: OverridesIn = Field(default_factory=OverridesIn)


class MuscleOverrideOut(_Out):
    priority: Priority | None = None
    weekly_min: float | None = None
    weekly_max: float | None = None


class TagOverrideOut(_Out):
    effect: TagEffect | None = None
    points: float | None = None


class OverridesOut(_Out):
    muscles: dict[str, MuscleOverrideOut]
    tags: dict[str, TagOverrideOut]


class PreferencesOut(_Out):
    version: int
    equipment_order: list[str]
    max_session_minutes: float | None
    overrides: OverridesOut


# --- Scheda completa (§ 7) -------------------------------------------------------


class SplitRefOut(_Out):
    id: int
    code: str
    name: str


class BadgeOut(_Out):
    """Etichetta con simbolo visibile, con la nota dell'assegnazione."""

    tag_id: int
    code: str
    name: str
    symbol: str
    color: TagColor
    note: str | None


class SlotExerciseOut(_Out):
    id: int
    code: str
    name: str
    equipment: str
    kind: Kind
    is_active: bool
    badges: list[BadgeOut]


class FamilyRefOut(_Out):
    id: int
    code: str
    name: str


class SlotOut(_Out):
    """Slot con esercizio, variante della seconda seduta e valori derivati."""

    id: int
    position: int
    family: FamilyRefOut
    exercise: SlotExerciseOut | None
    second_exercise: SlotExerciseOut | None
    sets: int
    rep_min: int
    rep_max: int
    is_optional: bool
    weekly_weight: float
    locked: bool
    note: str | None
    rest_seconds: int | None
    rir: str | None
    last_set_to_failure: bool | None


class DayStretchOut(_Out):
    id: int
    code: str
    name: str
    dose: str


class DayOut(_Out):
    id: int
    name: str
    position: int
    times_per_week: int
    stretches: list[DayStretchOut]
    slots: list[SlotOut]


class VolumeOut(_Out):
    """Volume settimanale di un muscolo con priorità e fascia effettive."""

    muscle_id: int
    code: str
    name: str
    short_name: str
    group_code: str
    volume: float
    priority: Priority
    weekly_min: float | None
    weekly_max: float | None
    status: str | None
    overridden: bool


class MuscleVolumeRefOut(_Out):
    muscle_id: int
    volume: float


class SessionOut(_Out):
    """Seduta concreta: due per i giorni con una variante della seconda seduta."""

    day_id: int
    session: int
    minutes: float
    max_muscle_volume: MuscleVolumeRefOut | None


class WarningOut(_Out):
    """Avviso (algoritmo, § 8); i campi valorizzati dipendono dal ``code``."""

    code: str
    day_id: int | None
    session: int | None
    slot_id: int | None
    position: int | None
    family_id: int | None
    muscle_id: int | None
    volume: float | None
    weekly_min: float | None
    weekly_max: float | None
    minutes: float | None
    excluded_by: list[str]


class AnalysisOut(_Out):
    volumes: list[VolumeOut]
    sessions: list[SessionOut]
    warnings: list[WarningOut]


class PlanOut(_Out):
    """La scheda completa: tutte le risposte che contengono una scheda hanno questa forma."""

    id: int
    name: str
    revision: int
    is_active: bool
    split: SplitRefOut | None
    created_at: datetime
    updated_at: datetime
    preferences: PreferencesOut
    days: list[DayOut]
    analysis: AnalysisOut


class PlanSummaryOut(_Out):
    """Riga dell'elenco delle schede (US-19 CA1)."""

    id: int
    name: str
    split_name: str | None
    days_per_week: int
    is_active: bool
    updated_at: datetime


# --- Richieste -------------------------------------------------------------------


class PlanCreateIn(BaseModel):
    """Con ``split_id``: copia lo split e genera. Con ``null``: scheda vuota."""

    split_id: int | None
    name: Label | None = None
    preferences: PreferencesIn | None = None


class PlanRenameIn(BaseModel):
    name: Label
