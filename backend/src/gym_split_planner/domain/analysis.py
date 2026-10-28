"""Analisi completa di una scheda: volumi, sedute e avvisi (algoritmo, § 2, 6 e 8)."""

from dataclasses import dataclass, field

from gym_split_planner.domain.duration import DurationParams, day_minutes
from gym_split_planner.domain.enums import BandStatus
from gym_split_planner.domain.model import Catalog, LevelWeights, MuscleTarget, PlanShape
from gym_split_planner.domain.scoring import Preferences
from gym_split_planner.domain.volume import (
    band_status,
    effective_targets,
    session_volumes,
    weekly_volume,
)


@dataclass(frozen=True)
class AnalysisSettings:
    """Impostazioni globali che servono all'analisi."""

    level_weights: LevelWeights = field(default_factory=LevelWeights)
    session_cap: float = 10
    duration: DurationParams = field(default_factory=DurationParams)
    max_session_minutes: float | None = 75


@dataclass(frozen=True)
class MuscleVolume:
    muscle: str
    volume: float
    target: MuscleTarget
    """Priorità e fascia effettive."""
    status: BandStatus | None
    overridden: bool


@dataclass(frozen=True)
class SessionInfo:
    day: str
    session: int
    minutes: float
    max_muscle: str | None
    max_volume: float


@dataclass(frozen=True)
class PlanWarning:
    """Avviso della scheda; i campi valorizzati dipendono dal ``code`` (§ 8)."""

    code: str
    day: str | None = None
    session: int | None = None
    position: int | None = None
    family: str | None = None
    muscle: str | None = None
    volume: float | None = None
    minutes: float | None = None


@dataclass(frozen=True)
class Analysis:
    volumes: list[MuscleVolume]
    sessions: list[SessionInfo]
    warnings: list[PlanWarning]


def analyze(
    plan: PlanShape,
    catalog: Catalog,
    preferences: Preferences,
    settings: AnalysisSettings | None = None,
) -> Analysis:
    """Volumi con stato rispetto alla fascia effettiva, sedute con durata, avvisi."""
    settings = settings or AnalysisSettings()
    totals = weekly_volume(plan, catalog, settings.level_weights)
    targets = effective_targets(catalog, preferences.overrides)
    volumes = [
        MuscleVolume(
            code,
            totals[code],
            target,
            band_status(totals[code], target),
            code in preferences.overrides.muscles,
        )
        for code, target in targets.items()
    ]
    warnings = [
        PlanWarning(
            "volume-below" if v.status is BandStatus.BELOW else "volume-above",
            muscle=v.muscle,
            volume=v.volume,
        )
        for v in volumes
        if v.status in (BandStatus.BELOW, BandStatus.ABOVE)
    ]

    sessions = []
    for day in plan.days:
        minutes = day_minutes(day, catalog, settings.duration)
        per_session = session_volumes(day, catalog, settings.level_weights)
        for index, (duration, volume) in enumerate(zip(minutes, per_session, strict=True), 1):
            top = max(sorted(volume), key=lambda m: volume[m], default=None)
            sessions.append(
                SessionInfo(day.code, index, duration, top, volume[top] if top else 0.0)
            )
            warnings.extend(
                PlanWarning("session-cap", day=day.code, session=index, muscle=m, volume=v)
                for m, v in sorted(volume.items())
                if v > settings.session_cap
            )
            if settings.max_session_minutes is not None and duration > settings.max_session_minutes:
                warnings.append(
                    PlanWarning("session-too-long", day=day.code, session=index, minutes=duration)
                )
        warnings.extend(
            PlanWarning("empty-slot", day=day.code, position=position, family=slot.family)
            for position, slot in enumerate(day.slots, 1)
            if slot.exercise is None
        )
    return Analysis(volumes, sessions, warnings)
