"""Schemi di split e schede (API, § 6.4, § 6.5, § 7)."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from gym_split_planner.api.schemas.catalog import Kind, Priority, TagColor, TagEffect
from gym_split_planner.api.schemas.inputs import Label, LongText, reject_null

DayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


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

    model_config = ConfigDict(extra="forbid")

    split_id: int | None
    name: Label | None = None
    preferences: PreferencesIn | None = None


class PlanRenameIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Label


# --- Personalizzazioni (§ 8.1) ------------------------------------------------------


class MuscleValuesOut(_Out):
    priority: Priority | None
    weekly_min: float | None
    weekly_max: float | None


class MuscleSettingOut(_Out):
    """Un muscolo con i tre livelli: catalogo, personalizzazione, effettivo."""

    muscle_id: int
    code: str
    name: str
    short_name: str
    group_code: str
    catalog: MuscleValuesOut
    override: MuscleValuesOut
    effective: MuscleValuesOut


class TagValuesOut(_Out):
    effect: TagEffect | None
    points: float | None


class TagSettingOut(_Out):
    tag_id: int
    code: str
    name: str
    symbol: str
    color: TagColor
    catalog: TagValuesOut
    override: TagValuesOut
    effective: TagValuesOut


class PlanSettingsOut(_Out):
    """Vista della schermata delle preferenze (US-11)."""

    revision: int
    equipment_order: list[str]
    max_session_minutes: float | None
    muscles: list[MuscleSettingOut]
    tags: list[TagSettingOut]


# --- Giorni (§ 6.7) -----------------------------------------------------------------


class DayIn(BaseModel):
    """Giorno nuovo; senza ``position`` va in fondo."""

    model_config = ConfigDict(extra="forbid")

    name: DayName
    times_per_week: int = Field(ge=1, le=3)
    position: int | None = Field(default=None, ge=1)


class DayPatch(BaseModel):
    """Nome e volte a settimana. Scendendo a 1, le varianti della seconda seduta si tolgono."""

    model_config = ConfigDict(extra="forbid")

    name: DayName | None = None
    times_per_week: int | None = Field(default=None, ge=1, le=3)

    _not_null = field_validator("name", "times_per_week")(reject_null)


class DayOrderIn(BaseModel):
    """Tutti gli ``id`` dei giorni della scheda, nel nuovo ordine."""

    model_config = ConfigDict(extra="forbid")

    day_ids: list[int] = Field(max_length=50)


# --- Slot (§ 6.8) -------------------------------------------------------------------


class SlotIn(BaseModel):
    """Slot nuovo. Senza esercizio: il miglior candidato della famiglia. Senza serie e
    ripetizioni: 3 × 6-12 per i multiarticolari, 3 × 10-15 per l'isolamento."""

    model_config = ConfigDict(extra="forbid")

    family_id: int
    exercise_id: int | None = None
    sets: int | None = Field(default=None, ge=1, le=8)
    rep_min: int | None = Field(default=None, ge=1, le=100)
    rep_max: int | None = Field(default=None, ge=1, le=100)
    position: int | None = Field(default=None, ge=1)


class SlotPatch(BaseModel):
    """Modifica parziale di uno slot, tutta o niente (regole nel § 6.8)."""

    model_config = ConfigDict(extra="forbid")

    exercise_id: int | None = None
    second_exercise_id: int | None = None
    """``null`` toglie la variante della seconda seduta."""
    family_id: int | None = None
    sets: int | None = Field(default=None, ge=1, le=8)
    rep_min: int | None = Field(default=None, ge=1, le=100)
    rep_max: int | None = Field(default=None, ge=1, le=100)
    is_optional: bool | None = None
    weekly_weight: float | None = None
    """1 ogni settimana, 0,5 a settimane alterne."""
    locked: bool | None = None
    note: LongText = None

    @field_validator("weekly_weight")
    @classmethod
    def _weekly_weight(cls, value: float | None) -> float | None:
        if value is not None and value not in (0.5, 1):
            raise ValueError("Il peso settimanale è 1 oppure 0,5 (settimane alterne)")
        return value

    _not_null = field_validator(
        "exercise_id",
        "family_id",
        "sets",
        "rep_min",
        "rep_max",
        "is_optional",
        "weekly_weight",
        "locked",
    )(reject_null)


class SlotOrderIn(BaseModel):
    """Tutti gli ``id`` degli slot del giorno, nel nuovo ordine."""

    model_config = ConfigDict(extra="forbid")

    slot_ids: list[int] = Field(max_length=100)


class ScoreBreakdownOut(_Out):
    confidence: float
    equipment: float
    stretch: float
    family: float
    rank: float
    tags: float


class VolumeDeltaOut(_Out):
    muscle_id: int
    code: str
    delta: float


class CandidateOut(_Out):
    """Candidato con punteggio, motivi di esclusione ed effetto sul volume settimanale."""

    exercise_id: int
    code: str
    name: str
    equipment: str
    family_match: Literal["primary", "secondary", "other"]
    score: float
    score_breakdown: ScoreBreakdownOut
    badges: list[BadgeOut]
    excluded_by: list[str]
    volume_delta: list[VolumeDeltaOut]


class CandidatesOut(_Out):
    slot_id: int
    session: int
    current_exercise_id: int | None
    candidates: list[CandidateOut]


# --- Rigenerazione (§ 6.9, § 8.2) -----------------------------------------------------


class ExerciseRefOut(_Out):
    exercise_id: int
    name: str


class RegenerationChangeOut(_Out):
    """Uno slot che la rigenerazione cambierebbe."""

    slot_id: int
    day_id: int
    day_name: str
    position: int
    current: ExerciseRefOut | None
    proposed: ExerciseRefOut
    volume_delta: list[VolumeDeltaOut]


class RegenerationPreviewOut(_Out):
    """Differenze calcolate sulla ``revision`` indicata, senza modificare nulla."""

    revision: int
    changes: list[RegenerationChangeOut]
    locked_slots: int


class RegenerateIn(BaseModel):
    """Slot dell'anteprima da applicare, tutti o una parte."""

    model_config = ConfigDict(extra="forbid")

    slot_ids: list[int] = Field(min_length=1, max_length=200)
