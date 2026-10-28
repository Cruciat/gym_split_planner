"""Caricamento dei dati iniziali (dati iniziali, § 9).

Il seed si esegue **solo su un database vuoto**: rieseguirlo a ogni avvio
rimetterebbe nel catalogo ciò che è stato eliminato dall'interfaccia. Tutto avviene
in una transazione: o si carica tutto, o niente.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from gym_split_planner.db.models import (
    AppSetting,
    DailyRoutineItem,
    DayTemplate,
    DayTemplateStretch,
    Equipment,
    Exercise,
    ExerciseMuscle,
    ExerciseTag,
    MovementFamily,
    Muscle,
    MuscleGroup,
    Plan,
    SlotTemplate,
    Source,
    SplitTemplate,
    StretchExercise,
    Tag,
)
from gym_split_planner.db.seed.schema import (
    AnatomyFile,
    ExercisesFile,
    FamiliesFile,
    RoutinesFile,
    SettingsFile,
    SourcesFile,
    SplitsFile,
    TagsFile,
)
from gym_split_planner.db.session import make_session_factory

DATA_DIR = Path(__file__).parent / "data"


class SeedError(Exception):
    """Dati iniziali non validi: riferimento inesistente o file malformato."""


@dataclass(frozen=True)
class SeedReport:
    """Quante righe sono state caricate, per il messaggio all'avvio."""

    exercises: int
    families: int
    splits: int


def _read[M: BaseModel](data_dir: Path, name: str, model: type[M]) -> M:
    path = data_dir / name
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        return model.model_validate(raw)
    except (OSError, yaml.YAMLError, ValueError) as error:
        raise SeedError(f"{name}: {error}") from error


def _lookup[T](index: dict[str, T], code: str, what: str, where: str) -> T:
    try:
        return index[code]
    except KeyError:
        raise SeedError(f"{where}: {what} '{code}' inesistente") from None


def is_empty(session: Session) -> bool:
    """Vero se non c'è ancora nessun dato: né catalogo né schede."""
    for model in (MuscleGroup, Exercise, Plan):
        if session.scalar(select(func.count()).select_from(model)):
            return False
    return True


def load_seed(session: Session, data_dir: Path = DATA_DIR) -> SeedReport:
    """Inserisce tutti i dati iniziali nella sessione, senza commit."""
    anatomy = _read(data_dir, "anatomy.yaml", AnatomyFile)
    sources_file = _read(data_dir, "sources.yaml", SourcesFile)
    tags_file = _read(data_dir, "tags.yaml", TagsFile)
    families_file = _read(data_dir, "families.yaml", FamiliesFile)
    exercises_file = _read(data_dir, "exercises.yaml", ExercisesFile)
    routines = _read(data_dir, "routines.yaml", RoutinesFile)
    splits_file = _read(data_dir, "splits.yaml", SplitsFile)
    settings_file = _read(data_dir, "settings.yaml", SettingsFile)

    groups = {
        g.code: MuscleGroup(code=g.code, name=g.name, sort_order=i)
        for i, g in enumerate(anatomy.muscle_groups, 1)
    }
    muscles = {
        m.code: Muscle(
            code=m.code,
            name=m.name,
            short_name=m.short_name,
            group=_lookup(groups, m.group, "gruppo", f"muscolo {m.code}"),
            priority=m.priority,
            weekly_min=m.weekly_min,
            weekly_max=m.weekly_max,
            notes=m.notes,
            sort_order=i,
        )
        for i, m in enumerate(anatomy.muscles, 1)
    }
    equipment = {
        e.code: Equipment(code=e.code, name=e.name, sort_order=i)
        for i, e in enumerate(anatomy.equipment, 1)
    }
    sources = {s.code: Source(**s.model_dump()) for s in sources_file.sources}
    tags = {t.code: Tag(**t.model_dump(), sort_order=i) for i, t in enumerate(tags_file.tags, 1)}
    session.add_all([*groups.values(), *muscles.values(), *equipment.values()])
    session.add_all([*sources.values(), *tags.values()])
    session.flush()

    families = {
        f.code: MovementFamily(
            code=f.code,
            name=f.name,
            description=f.description,
            muscle_group_id=_lookup(groups, f.group, "gruppo", f"famiglia {f.code}").id,
            sort_order=i,
        )
        for i, f in enumerate(families_file.families, 1)
    }
    session.add_all(families.values())
    session.flush()

    for e in exercises_file.exercises:
        where = f"esercizio {e.code}"
        exercise = Exercise(
            code=e.code,
            name=e.name,
            primary_family=_lookup(families, e.family, "famiglia", where),
            secondary_family=(
                _lookup(families, e.secondary_family, "famiglia", where)
                if e.secondary_family
                else None
            ),
            family_rank=e.family_rank,
            equipment=_lookup(equipment, e.equipment, "attrezzo", where),
            equipment_detail=e.equipment_detail,
            kind=e.kind,
            stretch=e.stretch,
            stretch_note=e.stretch_note,
            confidence=e.confidence,
            notes=e.notes,
        )
        exercise.muscles = [
            ExerciseMuscle(muscle=_lookup(muscles, code, "muscolo", where), level=level)
            for code, level in e.muscles.items()
        ]
        exercise.tags = [
            ExerciseTag(tag=_lookup(tags, t.tag, "etichetta", where), note=t.note) for t in e.tags
        ]
        exercise.sources = [_lookup(sources, code, "fonte", where) for code in e.sources]
        session.add(exercise)

    stretches = {s.code: StretchExercise(**s.model_dump()) for s in routines.stretches}
    session.add_all(stretches.values())
    session.add_all(DailyRoutineItem(**item.model_dump()) for item in routines.daily_routine)
    session.flush()

    for i, split_in in enumerate(splits_file.splits, 1):
        split = SplitTemplate(
            code=split_in.code,
            name=split_in.name,
            description=split_in.description,
            is_builtin=True,
            sort_order=i,
        )
        for day_position, day_in in enumerate(split_in.days, 1):
            where = f"split {split_in.code}, giorno {day_in.code}"
            day = DayTemplate(
                code=day_in.code,
                name=day_in.name,
                position=day_position,
                times_per_week=day_in.times_per_week,
            )
            day.slots = [
                SlotTemplate(
                    position=slot_position,
                    family_id=_lookup(families, s.family, "famiglia", where).id,
                    default_sets=s.sets,
                    rep_min=s.reps[0],
                    rep_max=s.reps[1],
                    is_optional=s.optional,
                    weekly_weight=s.weekly_weight,
                    note=s.note,
                )
                for slot_position, s in enumerate(day_in.slots, 1)
            ]
            day.stretches = [
                DayTemplateStretch(
                    stretch_id=_lookup(stretches, code, "stretch", where).id, position=p
                )
                for p, code in enumerate(day_in.stretches, 1)
            ]
            split.days.append(day)
        session.add(split)

    session.add_all(AppSetting(key=k, value=v) for k, v in settings_file.settings.items())
    session.flush()
    return SeedReport(
        exercises=len(exercises_file.exercises),
        families=len(families),
        splits=len(splits_file.splits),
    )


def seed_if_empty(engine: Engine, data_dir: Path = DATA_DIR) -> SeedReport | None:
    """Carica i dati iniziali se il database è vuoto; ``None`` se c'erano già dati."""
    with make_session_factory(engine)() as session, session.begin():
        if not is_empty(session):
            return None
        return load_seed(session, data_dir)
