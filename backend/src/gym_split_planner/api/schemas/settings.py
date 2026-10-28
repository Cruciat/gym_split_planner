"""Impostazioni globali (API, § 6.1; modello dati, § 5; algoritmo, § 3 e § 6)."""

from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


class _Strict(BaseModel):
    """Struttura fissa: chiavi sconosciute rifiutate, risposte costruite da dizionari."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class LevelWeightsIO(_Strict):
    """Valore delle serie per un muscolo primario (P) e secondario (S)."""

    P: float = Field(gt=0, le=2)
    S: float = Field(ge=0, le=2)

    @model_validator(mode="after")
    def _secondary_not_above_primary(self) -> Self:
        if self.S > self.P:
            raise ValueError("Il peso di S non può superare quello di P")
        return self


class ScoreWeightsIO(_Strict):
    """Pesi della base del punteggio (algoritmo, § 3.2)."""

    confidence: float = Field(ge=0, le=20)
    equipment: float = Field(ge=0, le=20)
    stretch: float = Field(ge=0, le=20)
    family: float = Field(ge=0, le=20)
    rank: float = Field(ge=0, le=20)


class DurationParamsIO(_Strict):
    """Parametri della stima della durata delle sedute (algoritmo, § 6.1)."""

    set_seconds: float = Field(gt=0, le=300)
    rest_compound_seconds: float = Field(ge=0, le=600)
    rest_isolation_seconds: float = Field(ge=0, le=600)
    change_seconds: float = Field(ge=0, le=600)
    warmup_set_seconds: float = Field(ge=0, le=300)
    warmup_rest_seconds: float = Field(ge=0, le=600)
    warmup_minutes: float = Field(ge=0, le=60)
    stretching_minutes: float = Field(ge=0, le=60)


class EffortIO(_Strict):
    """Intensità indicata nel PDF: RIR obiettivo e ultima serie a cedimento."""

    rir: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{1,2}(-\d{1,2})?$")]
    failure_last_set: bool


class SettingsIO(_Strict):
    """Tutte le impostazioni globali: il ``PUT`` le sostituisce insieme."""

    level_weights: LevelWeightsIO
    session_cap: float = Field(gt=0, le=50)
    score_weights: ScoreWeightsIO
    duration_params: DurationParamsIO
    warmup_text: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]
    effort: EffortIO
