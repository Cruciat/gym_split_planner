"""Schede: split predefiniti, creazione e generazione, gestione (US-10, US-12, US-19).

Ogni modifica di una scheda passa da ``modify_plan``: controlla la revisione su cui
il client lavorava, applica la modifica, incrementa la revisione e restituisce la
scheda completa (API, § 4). Le operazioni che non contano come modifica della scheda
(eliminazione, attivazione) non chiedono la revisione.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import Engine, select, update
from sqlalchemy.orm import Session, selectinload

from gym_split_planner.db.models import (
    DayTemplate,
    Exercise,
    Plan,
    PlanDay,
    PlanDayStretch,
    PlanSlot,
    SlotTemplate,
    SplitTemplate,
)
from gym_split_planner.db.repository import (
    equipment_order,
    load_catalog,
    load_plan,
    load_score_weights,
    load_split_shape,
)
from gym_split_planner.db.session import make_session_factory
from gym_split_planner.db.types import utc_now
from gym_split_planner.domain.generation import generate
from gym_split_planner.domain.preferences import (
    default_preferences,
    normalize_preferences,
    plan_preferences,
)
from gym_split_planner.services.errors import (
    NotFoundError,
    RevisionMismatchError,
    RuleError,
    RuleViolationError,
)
from gym_split_planner.services.plan_view import PlanViewData, build_plan_view

EMPTY_PLAN_NAME = "Scheda vuota"
COPY_SUFFIX = " (copia)"


# --- Split predefiniti (API, § 6.4) ------------------------------------------------


@dataclass(frozen=True)
class SplitFamilyData:
    id: int
    code: str
    name: str


@dataclass(frozen=True)
class SplitSlotData:
    family: SplitFamilyData
    sets: int
    rep_min: int
    rep_max: int
    is_optional: bool
    weekly_weight: float
    note: str | None


@dataclass(frozen=True)
class SplitDayData:
    name: str
    times_per_week: int
    slots: tuple[SplitSlotData, ...]


@dataclass(frozen=True)
class SplitData:
    id: int
    code: str
    name: str
    description: str | None
    days_per_week: int
    days: tuple[SplitDayData, ...]


def list_splits(engine: Engine) -> tuple[SplitData, ...]:
    """Preset per la procedura guidata (US-10 CA1), nell'ordine del catalogo."""
    with make_session_factory(engine)() as session:
        splits = session.scalars(
            select(SplitTemplate)
            .order_by(SplitTemplate.sort_order)
            .options(
                selectinload(SplitTemplate.days)
                .selectinload(DayTemplate.slots)
                .selectinload(SlotTemplate.family)
            )
        )
        return tuple(
            SplitData(
                id=split.id,
                code=split.code,
                name=split.name,
                description=split.description,
                days_per_week=sum(day.times_per_week for day in split.days),
                days=tuple(
                    SplitDayData(
                        name=day.name,
                        times_per_week=day.times_per_week,
                        slots=tuple(
                            SplitSlotData(
                                family=SplitFamilyData(
                                    slot.family.id, slot.family.code, slot.family.name
                                ),
                                sets=slot.default_sets,
                                rep_min=slot.rep_min,
                                rep_max=slot.rep_max,
                                is_optional=slot.is_optional,
                                weekly_weight=slot.weekly_weight,
                                note=slot.note,
                            )
                            for slot in day.slots
                        ),
                    )
                    for day in split.days
                ),
            )
            for split in splits
        )


# --- Elenco (US-19 CA1) ------------------------------------------------------------


@dataclass(frozen=True)
class PlanSummaryData:
    id: int
    name: str
    revision: int
    split_name: str | None
    days_per_week: int
    is_active: bool
    updated_at: Any


def list_plans(engine: Engine) -> tuple[PlanSummaryData, ...]:
    """Schede dalla modificata più di recente."""
    with make_session_factory(engine)() as session:
        plans = session.scalars(
            select(Plan)
            .order_by(Plan.updated_at.desc(), Plan.id.desc())
            .options(selectinload(Plan.days), selectinload(Plan.split_template))
        )
        return tuple(
            PlanSummaryData(
                id=plan.id,
                name=plan.name,
                revision=plan.revision,
                split_name=plan.split_template.name if plan.split_template else None,
                days_per_week=sum(day.times_per_week for day in plan.days),
                is_active=plan.is_active,
                updated_at=plan.updated_at,
            )
            for plan in plans
        )


# --- Creazione (US-10, US-11, US-12) ----------------------------------------------


def create_plan(
    engine: Engine,
    split_id: int | None,
    name: str | None,
    preferences: Mapping[str, Any] | None,
    today: date | None = None,
) -> PlanViewData:
    """Scheda nuova da uno split (copiato e generato) oppure vuota.

    Le preferenze facoltative si normalizzano come nel salvataggio (modello dati,
    § 4.7) e guidano già la prima generazione.
    """
    today = today or date.today()
    with make_session_factory(engine)() as session:
        split = None
        if split_id is not None:
            split = session.get(SplitTemplate, split_id)
            if split is None:
                raise RuleViolationError(
                    (RuleError("unknown-reference", "split_id", "Lo split scelto non esiste."),)
                )
        stored = validated_preferences(session, preferences)
        prefix = split.name if split else EMPTY_PLAN_NAME
        plan = Plan(
            name=name or f"{prefix} — {today:%d/%m/%Y}",
            split_template_id=split.id if split else None,
            preferences=stored,
        )
        if split is not None:
            _copy_split(session, plan, split, stored)
        session.add(plan)
        session.commit()
        return _view(session, plan.id)


def validated_preferences(
    session: Session, preferences: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Preferenze normalizzate e valide sui valori effettivi, o ``rule-violation``."""
    order = equipment_order(session)
    if preferences is None:
        return default_preferences(order)
    catalog = load_catalog(session)
    stored, violations = normalize_preferences(preferences, catalog.muscles, catalog.tags, order)
    if violations:
        raise RuleViolationError(tuple(RuleError(v.rule, v.field, v.message) for v in violations))
    return stored


def _copy_split(
    session: Session, plan: Plan, split: SplitTemplate, preferences: Mapping[str, Any]
) -> None:
    """Copia giorni, slot e stretching dello split, con gli esercizi della generazione."""
    catalog = load_catalog(session)
    prefs = plan_preferences(preferences, equipment_order(session))
    generated, _empty = generate(
        load_split_shape(session, split.code), catalog, prefs.scoring, load_score_weights(session)
    )
    exercise_ids: dict[str, int] = dict(session.execute(select(Exercise.code, Exercise.id)).all())
    days = session.scalars(
        select(DayTemplate)
        .where(DayTemplate.split_id == split.id)
        .order_by(DayTemplate.position)
        .options(selectinload(DayTemplate.slots), selectinload(DayTemplate.stretches))
    ).all()
    for template, shaped in zip(days, generated.days, strict=True):
        day = PlanDay(
            name=template.name,
            position=template.position,
            times_per_week=template.times_per_week,
        )
        for position, (slot_template, slot) in enumerate(
            zip(template.slots, shaped.slots, strict=True), 1
        ):
            day.slots.append(
                PlanSlot(
                    position=position,
                    family_id=slot_template.family_id,
                    exercise_id=exercise_ids[slot.exercise] if slot.exercise else None,
                    sets=slot_template.default_sets,
                    rep_min=slot_template.rep_min,
                    rep_max=slot_template.rep_max,
                    is_optional=slot_template.is_optional,
                    weekly_weight=slot_template.weekly_weight,
                    locked=False,
                    note=slot_template.note,
                )
            )
        day.stretches.extend(
            PlanDayStretch(stretch_id=link.stretch_id, position=link.position)
            for link in template.stretches
        )
        plan.days.append(day)


# --- Lettura e modifiche ---------------------------------------------------------


def get_plan(engine: Engine, plan_id: int) -> PlanViewData:
    with make_session_factory(engine)() as session:
        return _view(session, plan_id)


def modify_plan(
    engine: Engine,
    plan_id: int,
    expected_revision: int,
    change: Callable[[Session, Plan], None],
) -> PlanViewData:
    """Applica ``change`` se la revisione coincide; poi revisione + 1 e scheda completa."""
    with make_session_factory(engine)() as session:
        # Solo la riga della scheda: giorni e slot si caricano se la modifica li usa.
        plan = session.get(Plan, plan_id)
        if plan is None:
            raise NotFoundError("Scheda non trovata", f"Non esiste la scheda {plan_id}.")
        if plan.revision != expected_revision:
            raise RevisionMismatchError(plan.revision)
        change(session, plan)
        plan.revision += 1
        plan.updated_at = utc_now()
        session.commit()
        return _view(session, plan_id)


def rename_plan(engine: Engine, plan_id: int, name: str, expected_revision: int) -> PlanViewData:
    def change(_session: Session, plan: Plan) -> None:
        plan.name = name

    return modify_plan(engine, plan_id, expected_revision, change)


def delete_plan(engine: Engine, plan_id: int) -> None:
    """Elimina la scheda con giorni e slot; la conferma è dell'interfaccia (US-19 CA2)."""
    with make_session_factory(engine)() as session:
        session.delete(load_existing(session, plan_id))
        session.commit()


def duplicate_plan(engine: Engine, plan_id: int) -> PlanViewData:
    """Copia completa, non attiva, con il nome seguito da "(copia)"."""
    with make_session_factory(engine)() as session:
        source = load_existing(session, plan_id)
        copy = Plan(
            name=_copy_name(source.name),
            split_template_id=source.split_template_id,
            preferences=dict(source.preferences),
        )
        for day in source.days:
            new_day = PlanDay(
                name=day.name, position=day.position, times_per_week=day.times_per_week
            )
            new_day.slots.extend(
                PlanSlot(
                    position=slot.position,
                    family_id=slot.family_id,
                    exercise_id=slot.exercise_id,
                    second_exercise_id=slot.second_exercise_id,
                    sets=slot.sets,
                    rep_min=slot.rep_min,
                    rep_max=slot.rep_max,
                    is_optional=slot.is_optional,
                    weekly_weight=slot.weekly_weight,
                    locked=slot.locked,
                    note=slot.note,
                )
                for slot in day.slots
            )
            new_day.stretches.extend(
                PlanDayStretch(stretch_id=link.stretch_id, position=link.position)
                for link in day.stretches
            )
            copy.days.append(new_day)
        session.add(copy)
        session.commit()
        return _view(session, copy.id)


def activate_plan(engine: Engine, plan_id: int) -> PlanViewData:
    """La rende l'unica scheda attiva. Non è una modifica della scheda: la revisione resta."""
    with make_session_factory(engine)() as session:
        load_existing(session, plan_id)
        # Prima si spengono tutte, poi si accende questa: l'indice unico parziale
        # non tollera due schede attive nemmeno per un istante.
        session.execute(update(Plan).where(Plan.is_active.is_(True)).values(is_active=False))
        session.execute(update(Plan).where(Plan.id == plan_id).values(is_active=True))
        session.commit()
        session.expire_all()
        return _view(session, plan_id)


# --- Dettagli --------------------------------------------------------------------


def load_existing(session: Session, plan_id: int) -> Plan:
    plan = load_plan(session, plan_id)
    if plan is None:
        raise NotFoundError("Scheda non trovata", f"Non esiste la scheda {plan_id}.")
    return plan


def _view(session: Session, plan_id: int) -> PlanViewData:
    session.expire_all()
    return build_plan_view(session, load_existing(session, plan_id))


def _copy_name(name: str, max_length: int = 160) -> str:
    return name[: max_length - len(COPY_SUFFIX)] + COPY_SUFFIX
