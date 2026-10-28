"""Creazione, modifica ed eliminazione degli esercizi (US-03, US-04, US-05; API, § 6.3).

Le regole che attraversano più campi stanno nel dominio (``check_exercise``); qui si
aggiungono quelle che richiedono il database: riferimenti esistenti, nome e codice
liberi, utilizzi nelle schede.
"""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import Engine, func, or_, select
from sqlalchemy.orm import Session, selectinload

from gym_split_planner.db.models import (
    Equipment,
    Exercise,
    ExerciseMuscle,
    ExerciseTag,
    MovementFamily,
    Muscle,
    Plan,
    PlanDay,
    PlanSlot,
    Source,
    Tag,
)
from gym_split_planner.db.session import make_session_factory
from gym_split_planner.db.types import utc_now
from gym_split_planner.domain.catalog_rules import (
    check_exercise,
    is_valid_code,
    slugify,
    unique_code,
)
from gym_split_planner.domain.enums import Confidence, Kind, Level, Stretch
from gym_split_planner.services.catalog import (
    ExerciseDetailData,
    MuscleLinkData,
    TagLinkData,
    get_exercise_detail,
)
from gym_split_planner.services.errors import (
    InUseError,
    NotFoundError,
    RuleError,
    RuleViolationError,
)

CODE_MAX_LENGTH = 60


@dataclass(frozen=True)
class ExerciseInput:
    """Tutti i campi modificabili di un esercizio: la form li invia sempre tutti."""

    name: str
    primary_family_id: int
    secondary_family_id: int | None
    family_rank: int
    equipment_id: int
    equipment_detail: str | None
    kind: str
    stretch: str
    stretch_note: str | None
    confidence: str
    notes: str | None
    is_active: bool
    muscles: tuple[MuscleLinkData, ...]
    tags: tuple[TagLinkData, ...]
    source_ids: tuple[int, ...]


@dataclass(frozen=True)
class PlanUsageData:
    """Scheda che usa l'esercizio, con quanti slot (principale o seconda seduta)."""

    id: int
    name: str
    slots: int


@dataclass(frozen=True)
class ExerciseUsageData:
    """Dove è usato un esercizio (API, § 6.3, "Utilizzi")."""

    plans: tuple[PlanUsageData, ...]


# --- Casi d'uso ------------------------------------------------------------------


def create_exercise(
    engine: Engine, data: ExerciseInput, code: str | None = None
) -> ExerciseDetailData:
    """Crea un esercizio. Senza ``code`` lo genera dal nome, libero e immutabile."""
    with make_session_factory(engine)() as session:
        errors = _check(session, data, exercise_id=None)
        taken = set(session.scalars(select(Exercise.code)))
        if code is None:
            code = unique_code(
                slugify(data.name, max_length=CODE_MAX_LENGTH), taken, max_length=CODE_MAX_LENGTH
            )
        elif not is_valid_code(code) or len(code) > CODE_MAX_LENGTH:
            errors.append(
                RuleError(
                    "invalid-code",
                    "code",
                    "Il codice può contenere solo minuscole, cifre e trattini tra le parole.",
                )
            )
        elif code in taken:
            errors.append(RuleError("code-taken", "code", f"Il codice «{code}» è già usato."))
        if errors:
            raise RuleViolationError(tuple(errors))

        exercise = Exercise(code=code)
        _apply(session, exercise, data)
        session.add(exercise)
        session.commit()
        exercise_id = exercise.id
    return _detail(engine, exercise_id)


def replace_exercise(engine: Engine, exercise_id: int, data: ExerciseInput) -> ExerciseDetailData:
    """Sostituisce tutti i campi dell'esercizio; il ``code`` resta quello di creazione."""
    with make_session_factory(engine)() as session:
        exercise = _load(session, exercise_id)
        errors = _check(session, data, exercise_id=exercise_id)
        if errors:
            raise RuleViolationError(tuple(errors))
        _apply(session, exercise, data)
        # Anche se cambiano solo muscoli, etichette o fonti, l'esercizio è stato modificato.
        exercise.updated_at = utc_now()
        session.commit()
    return _detail(engine, exercise_id)


def get_exercise_usage(engine: Engine, exercise_id: int) -> ExerciseUsageData:
    """Schede che usano l'esercizio, come principale o come variante della seconda seduta."""
    with make_session_factory(engine)() as session:
        _load(session, exercise_id)
        return _usage(session, exercise_id)


def delete_exercise(engine: Engine, exercise_id: int) -> None:
    """Elimina un esercizio mai usato; se è in una scheda si può solo disattivare (US-05)."""
    with make_session_factory(engine)() as session:
        exercise = _load(session, exercise_id)
        usage = _usage(session, exercise_id)
        if usage.plans:
            names = ", ".join(f"«{plan.name}»" for plan in usage.plans)
            raise InUseError(
                "Esercizio in uso",
                f"L'esercizio è usato nelle schede {names}: si può solo disattivare.",
                {"plans": [{"id": p.id, "name": p.name, "slots": p.slots} for p in usage.plans]},
            )
        session.delete(exercise)
        session.commit()


# --- Dettagli --------------------------------------------------------------------


def _load(session: Session, exercise_id: int) -> Exercise:
    exercise = session.scalars(
        select(Exercise)
        .where(Exercise.id == exercise_id)
        .options(
            selectinload(Exercise.muscles),
            selectinload(Exercise.tags),
            selectinload(Exercise.sources),
        )
    ).one_or_none()
    if exercise is None:
        raise NotFoundError("Esercizio non trovato", f"Non esiste l'esercizio {exercise_id}.")
    return exercise


def _detail(engine: Engine, exercise_id: int) -> ExerciseDetailData:
    detail = get_exercise_detail(engine, exercise_id)
    assert detail is not None, "esercizio appena salvato"
    return detail


def _ids(session: Session, model: type[Muscle | Tag | Source | MovementFamily]) -> set[int]:
    return set(session.scalars(select(model.id)))


def _check(session: Session, data: ExerciseInput, exercise_id: int | None) -> list[RuleError]:
    """Tutte le regole violate, del dominio e del database, in un elenco solo."""
    errors = [
        RuleError(v.rule, v.field, v.message)
        for v in check_exercise(
            {m.muscle_id: Level(m.level) for m in data.muscles},
            data.primary_family_id,
            data.secondary_family_id,
        )
    ]

    families = _ids(session, MovementFamily)
    if data.primary_family_id not in families:
        errors.append(_unknown("primary_family_id", "La famiglia principale non esiste."))
    if data.secondary_family_id is not None and data.secondary_family_id not in families:
        errors.append(_unknown("secondary_family_id", "La famiglia secondaria non esiste."))
    if session.get(Equipment, data.equipment_id) is None:
        errors.append(_unknown("equipment_id", "L'attrezzo non esiste."))
    if not {m.muscle_id for m in data.muscles} <= _ids(session, Muscle):
        errors.append(_unknown("muscles", "Uno dei muscoli non esiste."))
    if not {t.tag_id for t in data.tags} <= _ids(session, Tag):
        errors.append(_unknown("tags", "Una delle etichette non esiste."))
    if not set(data.source_ids) <= _ids(session, Source):
        errors.append(_unknown("source_ids", "Una delle fonti non esiste."))

    if _has_duplicates(m.muscle_id for m in data.muscles):
        errors.append(
            RuleError("duplicate-muscle", "muscles", "Un muscolo compare più di una volta.")
        )
    if _has_duplicates(t.tag_id for t in data.tags):
        errors.append(RuleError("duplicate-tag", "tags", "Un'etichetta compare più di una volta."))

    same_name = select(Exercise.id).where(func.lower(Exercise.name) == data.name.lower())
    if exercise_id is not None:
        same_name = same_name.where(Exercise.id != exercise_id)
    if session.scalars(same_name).first() is not None:
        errors.append(
            RuleError("name-taken", "name", f"Esiste già un esercizio chiamato «{data.name}».")
        )
    return errors


def _unknown(field: str, message: str) -> RuleError:
    return RuleError("unknown-reference", field, message)


def _has_duplicates(values: Iterable[int]) -> bool:
    return any(n > 1 for n in Counter(values).values())


def _apply(session: Session, exercise: Exercise, data: ExerciseInput) -> None:
    """Copia i campi sull'esercizio, aggiornando i collegamenti per differenza.

    Muscoli ed etichette hanno chiavi composte: rimuovere e reinserire la stessa
    coppia nella stessa transazione confonderebbe la sessione, quindi si aggiornano
    quelli rimasti, si tolgono quelli spariti e si aggiungono i nuovi.
    """
    exercise.name = data.name
    exercise.primary_family_id = data.primary_family_id
    exercise.secondary_family_id = data.secondary_family_id
    exercise.family_rank = data.family_rank
    exercise.equipment_id = data.equipment_id
    exercise.equipment_detail = data.equipment_detail
    exercise.kind = Kind(data.kind)
    exercise.stretch = Stretch(data.stretch)
    exercise.stretch_note = data.stretch_note
    exercise.confidence = Confidence(data.confidence)
    exercise.notes = data.notes
    exercise.is_active = data.is_active

    muscles = {m.muscle_id: m for m in data.muscles}
    current_muscles = {link.muscle_id: link for link in exercise.muscles}
    for muscle_id, link in current_muscles.items():
        if muscle_id not in muscles:
            exercise.muscles.remove(link)
    for muscle_id, m in muscles.items():
        existing = current_muscles.get(muscle_id)
        if existing is None:
            exercise.muscles.append(
                ExerciseMuscle(muscle_id=muscle_id, level=Level(m.level), note=m.note)
            )
        else:
            existing.level = Level(m.level)
            existing.note = m.note

    tags = {t.tag_id: t for t in data.tags}
    current_tags = {link.tag_id: link for link in exercise.tags}
    for tag_id, tag_link in current_tags.items():
        if tag_id not in tags:
            exercise.tags.remove(tag_link)
    for tag_id, t in tags.items():
        existing_tag = current_tags.get(tag_id)
        if existing_tag is None:
            exercise.tags.append(ExerciseTag(tag_id=tag_id, note=t.note))
        else:
            existing_tag.note = t.note

    source_ids = list(dict.fromkeys(data.source_ids))
    exercise.sources = list(session.scalars(select(Source).where(Source.id.in_(source_ids))))


def _usage(session: Session, exercise_id: int) -> ExerciseUsageData:
    rows = session.execute(
        select(Plan.id, Plan.name, func.count(PlanSlot.id))
        .join(PlanDay, PlanDay.plan_id == Plan.id)
        .join(PlanSlot, PlanSlot.plan_day_id == PlanDay.id)
        .where(or_(PlanSlot.exercise_id == exercise_id, PlanSlot.second_exercise_id == exercise_id))
        .group_by(Plan.id, Plan.name)
        .order_by(Plan.name)
    ).all()
    return ExerciseUsageData(tuple(PlanUsageData(id_, name, slots) for id_, name, slots in rows))
