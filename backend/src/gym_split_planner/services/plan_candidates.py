"""Candidati di uno slot con punteggio ed effetto sul volume (US-14, US-17; API, § 6.8).

Il calcolo è del dominio (algoritmo, § 3 e § 5); qui si traducono i codici in ``id``
e si aggiungono nome, attrezzo e simboli delle etichette di ogni candidato.
"""

from dataclasses import dataclass

from sqlalchemy import Engine, select
from sqlalchemy.orm import selectinload

from gym_split_planner.db.models import Exercise, ExerciseTag, Muscle
from gym_split_planner.db.repository import (
    day_code,
    equipment_order,
    load_catalog,
    load_level_weights,
    load_score_weights,
    plan_shape,
)
from gym_split_planner.db.session import make_session_factory
from gym_split_planner.domain.preferences import plan_preferences
from gym_split_planner.domain.preview import variant_previews
from gym_split_planner.services.errors import RuleError, RuleViolationError
from gym_split_planner.services.plan_edit import find_slot
from gym_split_planner.services.plan_view import BadgeData, slot_exercise
from gym_split_planner.services.plans import load_existing

FAMILY_MATCH = {1.0: "primary", 0.5: "secondary", 0.0: "other"}


@dataclass(frozen=True)
class ScoreBreakdownData:
    """Voci del punteggio, già pesate: la somma è ``score``."""

    confidence: float
    equipment: float
    stretch: float
    family: float
    rank: float
    tags: float


@dataclass(frozen=True)
class VolumeDeltaData:
    muscle_id: int
    code: str
    delta: float


@dataclass(frozen=True)
class CandidateData:
    exercise_id: int
    code: str
    name: str
    equipment: str
    family_match: str
    score: float
    score_breakdown: ScoreBreakdownData
    badges: tuple[BadgeData, ...]
    excluded_by: tuple[str, ...]
    volume_delta: tuple[VolumeDeltaData, ...]


@dataclass(frozen=True)
class CandidatesData:
    slot_id: int
    session: int
    current_exercise_id: int | None
    candidates: tuple[CandidateData, ...]


def slot_candidates(
    engine: Engine, plan_id: int, slot_id: int, session_number: int
) -> CandidatesData:
    """Candidati per l'esercizio principale (``1``) o per la seconda seduta (``2``).

    Ordine: non esclusi per punteggio, poi gli esclusi con il motivo. Con la seconda
    seduta, dopo la famiglia dello slot vengono tutti gli altri esercizi attivi.
    """
    with make_session_factory(engine)() as session:
        plan = load_existing(session, plan_id)
        slot, day = find_slot(plan, slot_id)
        if session_number == 2 and day.times_per_week < 2:
            raise RuleViolationError(
                (
                    RuleError(
                        "second-session-requires-repeat",
                        "session",
                        "La seconda seduta esiste solo nei giorni ripetuti almeno due volte.",
                    ),
                )
            )
        catalog = load_catalog(session)
        prefs = plan_preferences(plan.preferences, equipment_order(session))
        shape = plan_shape(plan)
        domain_day = next(d for d in shape.days if d.code == day_code(day))
        position = day.slots.index(slot) + 1
        previews = variant_previews(
            domain_day,
            position,
            catalog,
            prefs.scoring,
            session=session_number,
            score_weights=load_score_weights(session),
            level_weights=load_level_weights(session),
        )

        codes = [p.candidate.exercise for p in previews]
        exercises = {
            e.code: e
            for e in session.scalars(
                select(Exercise)
                .where(Exercise.code.in_(codes))
                .options(
                    selectinload(Exercise.tags).selectinload(ExerciseTag.tag),
                    selectinload(Exercise.equipment),
                )
            )
        }
        muscles: dict[str, int] = dict(session.execute(select(Muscle.code, Muscle.id)).all())

        result = []
        for preview in previews:
            candidate = preview.candidate
            exercise = exercises[candidate.exercise]
            info = slot_exercise(exercise)
            assert info is not None
            b = candidate.breakdown
            result.append(
                CandidateData(
                    exercise_id=exercise.id,
                    code=exercise.code,
                    name=exercise.name,
                    equipment=exercise.equipment.code,
                    family_match=FAMILY_MATCH.get(candidate.family_match, "other"),
                    score=round(candidate.score, 3),
                    score_breakdown=ScoreBreakdownData(
                        confidence=round(b.confidence, 3),
                        equipment=round(b.equipment, 3),
                        stretch=round(b.stretch, 3),
                        family=round(b.family, 3),
                        rank=round(b.rank, 3),
                        tags=round(b.tags, 3),
                    ),
                    badges=info.badges,
                    excluded_by=candidate.excluded_by,
                    volume_delta=tuple(
                        VolumeDeltaData(muscles[code], code, delta)
                        for code, delta in preview.volume_delta.items()
                    ),
                )
            )
        current = slot.second_exercise_id if session_number == 2 else slot.exercise_id
        return CandidatesData(slot.id, session_number, current, tuple(result))
