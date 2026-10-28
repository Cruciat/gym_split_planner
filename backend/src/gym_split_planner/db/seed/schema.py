"""Forma dei file YAML del seed, validata prima di scrivere nel database.

Ogni campo sconosciuto è un errore: un refuso nei dati deve fermare il caricamento,
non essere ignorato in silenzio.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gym_split_planner.domain.enums import (
    Confidence,
    Kind,
    Level,
    Priority,
    RoutineBlock,
    Stretch,
    TagColor,
    TagEffect,
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MuscleGroupIn(_Strict):
    code: str
    name: str


class MuscleIn(_Strict):
    code: str
    name: str
    short_name: str
    group: str
    priority: Priority
    weekly_min: float | None = None
    weekly_max: float | None = None
    notes: str | None = None


class EquipmentIn(_Strict):
    code: str
    name: str


class AnatomyFile(_Strict):
    muscle_groups: list[MuscleGroupIn]
    muscles: list[MuscleIn]
    equipment: list[EquipmentIn]


class SourceIn(_Strict):
    code: str
    title: str
    kind: str
    url: str | None = None
    reliability: str | None = None
    used_for: str | None = None


class SourcesFile(_Strict):
    sources: list[SourceIn]


class TagIn(_Strict):
    code: str
    name: str
    description: str | None = None
    symbol: str
    color: TagColor
    effect: TagEffect
    points: float = 0
    show_badge: bool = True


class TagsFile(_Strict):
    tags: list[TagIn]


class FamilyIn(_Strict):
    code: str
    name: str
    group: str
    description: str | None = None


class FamiliesFile(_Strict):
    families: list[FamilyIn]


class ExerciseTagIn(_Strict):
    tag: str
    note: str | None = None


class ExerciseIn(_Strict):
    code: str
    name: str
    family: str
    family_rank: int = Field(ge=1)
    secondary_family: str | None = None
    equipment: str
    equipment_detail: str | None = None
    kind: Kind
    stretch: Stretch
    stretch_note: str | None = None
    confidence: Confidence
    muscles: dict[str, Level]
    tags: list[ExerciseTagIn] = []
    sources: list[str] = []
    notes: str | None = None
    excel_id: str | None = None
    """Solo tracciabilità verso l'Excel: non viene salvato."""


class ExercisesFile(_Strict):
    exercises: list[ExerciseIn]


class StretchIn(_Strict):
    code: str
    name: str
    targets: str
    dose: str
    instructions: str | None = None
    confidence: Confidence | None = None
    note: str | None = None


class RoutineItemIn(_Strict):
    block: RoutineBlock
    position: int
    name: str
    dose: str
    purpose: str
    confidence: Confidence


class RoutinesFile(_Strict):
    stretches: list[StretchIn]
    daily_routine: list[RoutineItemIn]


class SlotIn(_Strict):
    family: str
    sets: int = Field(ge=1, le=8)
    reps: tuple[int, int]
    optional: bool = False
    weekly_weight: float = 1.0
    note: str | None = None

    @model_validator(mode="after")
    def _reps_in_order(self) -> "SlotIn":
        if not 1 <= self.reps[0] <= self.reps[1]:
            raise ValueError(f"Ripetizioni non valide: {self.reps}")
        return self


class DayIn(_Strict):
    code: str
    name: str
    times_per_week: int = Field(ge=1, le=3)
    stretches: list[str] = []
    slots: list[SlotIn]


class SplitIn(_Strict):
    code: str
    name: str
    description: str | None = None
    days: list[DayIn]


class SplitsFile(_Strict):
    splits: list[SplitIn]


class SettingsFile(_Strict):
    settings: dict[str, Any]
