"""Catalogo in lettura: tutto in blocco e dettaglio di un esercizio (API, § 6.2).

Il catalogo è piccolo (decine di muscoli e famiglie, meno di 500 esercizi anche in
futuro): si restituisce tutto in una volta e i filtri di US-01 si applicano nel client.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, selectinload

from gym_split_planner.db.models import (
    DailyRoutineItem,
    Equipment,
    Exercise,
    ExerciseMuscle,
    ExerciseTag,
    MovementFamily,
    Muscle,
    MuscleGroup,
    Source,
    StretchExercise,
    Tag,
)
from gym_split_planner.db.session import make_session_factory

# --- Forme restituite ------------------------------------------------------------
# Dataclass semplici: lo strato api le converte nei suoi schemi Pydantic.


@dataclass(frozen=True)
class MuscleGroupData:
    id: int
    code: str
    name: str
    sort_order: int


@dataclass(frozen=True)
class MuscleData:
    id: int
    code: str
    name: str
    short_name: str
    muscle_group_id: int
    priority: str
    weekly_min: float | None
    weekly_max: float | None
    notes: str | None
    sort_order: int


@dataclass(frozen=True)
class EquipmentData:
    id: int
    code: str
    name: str
    sort_order: int


@dataclass(frozen=True)
class FamilyData:
    id: int
    code: str
    name: str
    description: str | None
    muscle_group_id: int
    sort_order: int


@dataclass(frozen=True)
class TagData:
    id: int
    code: str
    name: str
    description: str | None
    symbol: str
    color: str
    effect: str
    points: float
    show_badge: bool
    sort_order: int


@dataclass(frozen=True)
class SourceData:
    id: int
    code: str
    title: str
    kind: str
    url: str | None
    reliability: str | None
    used_for: str | None


@dataclass(frozen=True)
class StretchData:
    id: int
    code: str
    name: str
    targets: str
    instructions: str | None
    dose: str
    confidence: str | None
    note: str | None


@dataclass(frozen=True)
class RoutineItemData:
    id: int
    block: str
    position: int
    name: str
    dose: str
    purpose: str
    confidence: str


@dataclass(frozen=True)
class MuscleLinkData:
    """Coinvolgimento di un muscolo: ``level`` P o S, ``note`` solo nel dettaglio."""

    muscle_id: int
    level: str
    note: str | None = None


@dataclass(frozen=True)
class TagLinkData:
    """Etichetta assegnata a un esercizio, con la nota di quell'assegnazione."""

    tag_id: int
    note: str | None


@dataclass(frozen=True)
class ExerciseSummaryData:
    """Riepilogo di un esercizio: basta per la lista e per tutti i filtri di US-01."""

    id: int
    code: str
    name: str
    primary_family_id: int
    secondary_family_id: int | None
    family_rank: int
    equipment_id: int
    equipment_detail: str | None
    kind: str
    stretch: str
    confidence: str
    is_active: bool
    muscles: tuple[MuscleLinkData, ...]
    tags: tuple[TagLinkData, ...]


@dataclass(frozen=True)
class CatalogData:
    """Tutto il catalogo (API, § 6.2)."""

    muscle_groups: tuple[MuscleGroupData, ...]
    muscles: tuple[MuscleData, ...]
    equipment: tuple[EquipmentData, ...]
    families: tuple[FamilyData, ...]
    tags: tuple[TagData, ...]
    exercises: tuple[ExerciseSummaryData, ...]
    sources: tuple[SourceData, ...]
    stretches: tuple[StretchData, ...]
    daily_routine: tuple[RoutineItemData, ...]


@dataclass(frozen=True)
class VariantData:
    """Altro esercizio attivo di una delle famiglie dell'esercizio (US-02)."""

    id: int
    code: str
    name: str
    family_id: int
    """Famiglia in comune con l'esercizio di cui si guarda il dettaglio."""
    equipment_id: int
    family_rank: int
    tags: tuple[TagLinkData, ...]


@dataclass(frozen=True)
class ExerciseDetailData:
    """Dettaglio di un esercizio (US-02): tutti i campi, fonti e varianti."""

    id: int
    code: str
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
    created_at: datetime
    updated_at: datetime
    muscles: tuple[MuscleLinkData, ...]
    tags: tuple[TagLinkData, ...]
    sources: tuple[SourceData, ...]
    variants: tuple[VariantData, ...]


# --- Casi d'uso ------------------------------------------------------------------


def get_catalog(engine: Engine) -> CatalogData:
    """Tutto il catalogo, compresi gli esercizi disattivati (il client li nasconde, US-01 CA4)."""
    with make_session_factory(engine)() as session:
        return _load_catalog(session)


def get_exercise_detail(engine: Engine, exercise_id: int) -> ExerciseDetailData | None:
    """Dettaglio dell'esercizio, o ``None`` se non esiste."""
    with make_session_factory(engine)() as session:
        exercise = session.scalars(
            select(Exercise)
            .where(Exercise.id == exercise_id)
            .options(
                selectinload(Exercise.muscles).selectinload(ExerciseMuscle.muscle),
                selectinload(Exercise.tags).selectinload(ExerciseTag.tag),
                selectinload(Exercise.sources),
            )
        ).one_or_none()
        if exercise is None:
            return None
        return ExerciseDetailData(
            id=exercise.id,
            code=exercise.code,
            name=exercise.name,
            primary_family_id=exercise.primary_family_id,
            secondary_family_id=exercise.secondary_family_id,
            family_rank=exercise.family_rank,
            equipment_id=exercise.equipment_id,
            equipment_detail=exercise.equipment_detail,
            kind=exercise.kind,
            stretch=exercise.stretch,
            stretch_note=exercise.stretch_note,
            confidence=exercise.confidence,
            notes=exercise.notes,
            is_active=exercise.is_active,
            created_at=exercise.created_at,
            updated_at=exercise.updated_at,
            muscles=_muscle_links(exercise, with_notes=True),
            tags=_tag_links(exercise),
            sources=tuple(_source(s) for s in sorted(exercise.sources, key=lambda s: s.code)),
            variants=_variants(session, exercise),
        )


# --- Conversioni -----------------------------------------------------------------


def _load_catalog(session: Session) -> CatalogData:
    exercises = session.scalars(
        select(Exercise)
        .options(
            selectinload(Exercise.muscles).selectinload(ExerciseMuscle.muscle),
            selectinload(Exercise.tags).selectinload(ExerciseTag.tag),
        )
        .order_by(Exercise.name)
    )
    return CatalogData(
        muscle_groups=tuple(
            MuscleGroupData(g.id, g.code, g.name, g.sort_order)
            for g in session.scalars(select(MuscleGroup).order_by(MuscleGroup.sort_order))
        ),
        muscles=tuple(
            MuscleData(
                id=m.id,
                code=m.code,
                name=m.name,
                short_name=m.short_name,
                muscle_group_id=m.muscle_group_id,
                priority=m.priority,
                weekly_min=m.weekly_min,
                weekly_max=m.weekly_max,
                notes=m.notes,
                sort_order=m.sort_order,
            )
            for m in session.scalars(select(Muscle).order_by(Muscle.sort_order))
        ),
        equipment=tuple(
            EquipmentData(e.id, e.code, e.name, e.sort_order)
            for e in session.scalars(select(Equipment).order_by(Equipment.sort_order))
        ),
        families=tuple(
            FamilyData(f.id, f.code, f.name, f.description, f.muscle_group_id, f.sort_order)
            for f in session.scalars(select(MovementFamily).order_by(MovementFamily.sort_order))
        ),
        tags=tuple(
            TagData(
                id=t.id,
                code=t.code,
                name=t.name,
                description=t.description,
                symbol=t.symbol,
                color=t.color,
                effect=t.effect,
                points=t.points,
                show_badge=t.show_badge,
                sort_order=t.sort_order,
            )
            for t in session.scalars(select(Tag).order_by(Tag.sort_order))
        ),
        exercises=tuple(
            ExerciseSummaryData(
                id=e.id,
                code=e.code,
                name=e.name,
                primary_family_id=e.primary_family_id,
                secondary_family_id=e.secondary_family_id,
                family_rank=e.family_rank,
                equipment_id=e.equipment_id,
                equipment_detail=e.equipment_detail,
                kind=e.kind,
                stretch=e.stretch,
                confidence=e.confidence,
                is_active=e.is_active,
                muscles=_muscle_links(e, with_notes=False),
                tags=_tag_links(e),
            )
            for e in exercises
        ),
        sources=tuple(_source(s) for s in session.scalars(select(Source).order_by(Source.code))),
        stretches=tuple(
            StretchData(
                id=s.id,
                code=s.code,
                name=s.name,
                targets=s.targets,
                instructions=s.instructions,
                dose=s.dose,
                confidence=s.confidence,
                note=s.note,
            )
            for s in session.scalars(select(StretchExercise).order_by(StretchExercise.id))
        ),
        daily_routine=tuple(
            RoutineItemData(r.id, r.block, r.position, r.name, r.dose, r.purpose, r.confidence)
            for r in session.scalars(select(DailyRoutineItem).order_by(DailyRoutineItem.position))
        ),
    )


def _muscle_links(exercise: Exercise, *, with_notes: bool) -> tuple[MuscleLinkData, ...]:
    """Coinvolgimenti in ordine di muscolo (``sort_order``), primari e secondari insieme."""
    links = sorted(exercise.muscles, key=lambda link: link.muscle.sort_order)
    return tuple(
        MuscleLinkData(link.muscle_id, link.level, link.note if with_notes else None)
        for link in links
    )


def _tag_links(exercise: Exercise) -> tuple[TagLinkData, ...]:
    """Etichette nell'ordine dei loro simboli (``tag.sort_order``)."""
    links = sorted(exercise.tags, key=lambda link: link.tag.sort_order)
    return tuple(TagLinkData(link.tag_id, link.note) for link in links)


def _source(source: Source) -> SourceData:
    return SourceData(
        id=source.id,
        code=source.code,
        title=source.title,
        kind=source.kind,
        url=source.url,
        reliability=source.reliability,
        used_for=source.used_for,
    )


def _variants(session: Session, exercise: Exercise) -> tuple[VariantData, ...]:
    """Gli altri esercizi attivi delle famiglie dell'esercizio (US-02 CA1).

    Prima quelli della famiglia principale, poi della secondaria. In ogni famiglia
    vengono prima gli esercizi che ce l'hanno come principale, in ordine di
    ``family_rank``, poi quelli che ce l'hanno come secondaria. Un esercizio che
    condivide entrambe le famiglie compare una volta sola, nella prima.
    """
    families = [exercise.primary_family_id]
    if exercise.secondary_family_id is not None:
        families.append(exercise.secondary_family_id)

    candidates = session.scalars(
        select(Exercise)
        .where(
            Exercise.id != exercise.id,
            Exercise.is_active.is_(True),
            (Exercise.primary_family_id.in_(families))
            | (Exercise.secondary_family_id.in_(families)),
        )
        .options(selectinload(Exercise.tags).selectinload(ExerciseTag.tag))
    ).all()

    seen: set[int] = set()
    variants: list[VariantData] = []
    for family_id in families:
        in_family = [
            c for c in candidates if family_id in (c.primary_family_id, c.secondary_family_id)
        ]
        in_family.sort(key=lambda c: (c.primary_family_id != family_id, c.family_rank, c.name))
        for candidate in in_family:
            if candidate.id in seen:
                continue
            seen.add(candidate.id)
            variants.append(
                VariantData(
                    id=candidate.id,
                    code=candidate.code,
                    name=candidate.name,
                    family_id=family_id,
                    equipment_id=candidate.equipment_id,
                    family_rank=candidate.family_rank,
                    tags=_tag_links(candidate),
                )
            )
    return tuple(variants)
