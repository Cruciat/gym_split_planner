"""Etichette: creazione, modifica, eliminazione, assegnazione (US-08; API, § 6.3; ADR 0014)."""

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Engine, delete, func, select
from sqlalchemy.orm import Session

from gym_split_planner.db.models import Exercise, ExerciseTag, Plan, Tag
from gym_split_planner.db.session import make_session_factory
from gym_split_planner.db.types import utc_now
from gym_split_planner.domain.catalog_rules import check_tag
from gym_split_planner.domain.enums import TagColor, TagEffect
from gym_split_planner.services.catalog import TagData
from gym_split_planner.services.common import name_taken, new_code, next_sort_order, unknown
from gym_split_planner.services.errors import (
    NotFoundError,
    PlanRef,
    RuleError,
    RuleViolationError,
)

EDITABLE = frozenset(
    {"name", "description", "symbol", "color", "effect", "points", "show_badge", "sort_order"}
)


@dataclass(frozen=True)
class TagInput:
    name: str
    description: str | None
    symbol: str
    color: str
    effect: str
    points: float
    show_badge: bool


@dataclass(frozen=True)
class TagUsageData:
    """Chi usa un'etichetta: serve alla conferma di eliminazione (US-08 CA3)."""

    exercises: int
    plans_with_overrides: tuple[PlanRef, ...]


def create_tag(engine: Engine, data: TagInput, code: str | None = None) -> TagData:
    """Crea un'etichetta; il suo simbolo va in fondo all'ordine."""
    with make_session_factory(engine)() as session:
        errors = _check(session, data.name, TagEffect(data.effect), data.points, exclude_id=None)
        tag_code, code_errors = new_code(session, Tag.code, data.name, code)
        errors += code_errors
        if errors:
            raise RuleViolationError(tuple(errors))
        tag = Tag(
            code=tag_code,
            name=data.name,
            description=data.description,
            symbol=data.symbol,
            color=TagColor(data.color),
            effect=TagEffect(data.effect),
            points=data.points,
            show_badge=data.show_badge,
            sort_order=next_sort_order(session, Tag.sort_order),
        )
        session.add(tag)
        session.commit()
        return _data(tag)


def update_tag(engine: Engine, tag_id: int, changes: Mapping[str, Any]) -> TagData:
    """Modifica parziale. Effetto e punti valgono subito per le schede che non li personalizzano;
    la generazione già fatta non cambia finché non si rigenera (US-08 CA4)."""
    unknown_fields = set(changes) - EDITABLE
    if unknown_fields:
        raise ValueError(f"Campi non modificabili: {sorted(unknown_fields)}")
    with make_session_factory(engine)() as session:
        tag = _load(session, tag_id)
        effect = TagEffect(changes.get("effect", tag.effect))
        points = float(changes.get("points", tag.points))
        errors = _check(session, changes.get("name", tag.name), effect, points, exclude_id=tag_id)
        if errors:
            raise RuleViolationError(tuple(errors))
        for field, value in changes.items():
            if field == "effect":
                tag.effect = TagEffect(value)
            elif field == "color":
                tag.color = TagColor(value)
            else:
                setattr(tag, field, value)
        session.commit()
        return _data(tag)


def get_tag_usage(engine: Engine, tag_id: int) -> TagUsageData:
    with make_session_factory(engine)() as session:
        tag = _load(session, tag_id)
        return _usage(session, tag)


def delete_tag(engine: Engine, tag_id: int) -> None:
    """Elimina l'etichetta, le sue assegnazioni e le personalizzazioni delle schede,
    in una transazione (modello dati, § 6)."""
    with make_session_factory(engine)() as session:
        tag = _load(session, tag_id)
        for plan in session.scalars(select(Plan)):
            preferences = plan.preferences
            tags = (preferences.get("overrides") or {}).get("tags")
            if isinstance(tags, dict) and tag.code in tags:
                overrides = dict(preferences["overrides"])
                overrides["tags"] = {code: v for code, v in tags.items() if code != tag.code}
                # Un dizionario nuovo: SQLAlchemy non vede le modifiche dentro una colonna JSON.
                plan.preferences = {**preferences, "overrides": overrides}
                plan.revision += 1
                plan.updated_at = utc_now()
        session.delete(tag)
        session.commit()


def assign_tag(
    engine: Engine, tag_id: int, exercise_ids: Collection[int], note: str | None, set_note: bool
) -> TagUsageData:
    """Assegna l'etichetta a più esercizi (US-08 CA2).

    La nota vale per tutti; a un esercizio che ha già l'etichetta la nota si
    aggiorna solo se ``set_note`` (cioè se la richiesta la conteneva).
    """
    with make_session_factory(engine)() as session:
        tag = _load(session, tag_id)
        ids = set(exercise_ids)
        _check_exercises(session, ids)
        existing = {
            link.exercise_id: link
            for link in session.scalars(
                select(ExerciseTag).where(
                    ExerciseTag.tag_id == tag_id, ExerciseTag.exercise_id.in_(ids)
                )
            )
        }
        for exercise_id in sorted(ids):
            link = existing.get(exercise_id)
            if link is None:
                session.add(ExerciseTag(exercise_id=exercise_id, tag_id=tag_id, note=note))
            elif set_note:
                link.note = note
        _touch(session, ids)
        session.commit()
        return _usage(session, tag)


def unassign_tag(engine: Engine, tag_id: int, exercise_ids: Collection[int]) -> TagUsageData:
    """Toglie l'etichetta dagli esercizi indicati; quelli che non l'avevano restano come sono."""
    with make_session_factory(engine)() as session:
        tag = _load(session, tag_id)
        ids = set(exercise_ids)
        _check_exercises(session, ids)
        session.execute(
            delete(ExerciseTag).where(
                ExerciseTag.tag_id == tag_id, ExerciseTag.exercise_id.in_(ids)
            )
        )
        _touch(session, ids)
        session.commit()
        return _usage(session, tag)


# --- Dettagli --------------------------------------------------------------------


def _load(session: Session, tag_id: int) -> Tag:
    tag = session.get(Tag, tag_id)
    if tag is None:
        raise NotFoundError("Etichetta non trovata", f"Non esiste l'etichetta {tag_id}.")
    return tag


def _check(
    session: Session, name: str, effect: TagEffect, points: float, exclude_id: int | None
) -> list[RuleError]:
    errors = [RuleError(v.rule, v.field, v.message) for v in check_tag(effect, points)]
    if name_taken(session, Tag.name, Tag.id, name, exclude_id):
        errors.append(RuleError("name-taken", "name", f"Esiste già un'etichetta «{name}»."))
    return errors


def _check_exercises(session: Session, ids: set[int]) -> None:
    found = set(session.scalars(select(Exercise.id).where(Exercise.id.in_(ids))))
    if found != ids:
        raise RuleViolationError(
            (unknown("exercise_ids", "Uno degli esercizi indicati non esiste."),)
        )


def _touch(session: Session, ids: set[int]) -> None:
    """Le etichette fanno parte dell'esercizio: assegnarle lo modifica."""
    for exercise in session.scalars(select(Exercise).where(Exercise.id.in_(ids))):
        exercise.updated_at = utc_now()


def _usage(session: Session, tag: Tag) -> TagUsageData:
    exercises = session.scalar(
        select(func.count()).select_from(ExerciseTag).where(ExerciseTag.tag_id == tag.id)
    )
    plans = tuple(
        PlanRef(plan.id, plan.name)
        for plan in session.scalars(select(Plan).order_by(Plan.name))
        if tag.code in ((plan.preferences.get("overrides") or {}).get("tags") or {})
    )
    return TagUsageData(exercises=int(exercises or 0), plans_with_overrides=plans)


def _data(tag: Tag) -> TagData:
    return TagData(
        id=tag.id,
        code=tag.code,
        name=tag.name,
        description=tag.description,
        symbol=tag.symbol,
        color=tag.color,
        effect=tag.effect,
        points=tag.points,
        show_badge=tag.show_badge,
        sort_order=tag.sort_order,
    )
