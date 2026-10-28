"""Dati iniziali: caricamento e validità (dati iniziali, § 9)."""

import csv
import shutil
from collections import Counter
from pathlib import Path

import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from gym_split_planner.db.models import (
    AppSetting,
    DailyRoutineItem,
    Equipment,
    Exercise,
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
from gym_split_planner.db.seed.loader import DATA_DIR, SeedError, load_seed, seed_if_empty
from gym_split_planner.db.session import make_session_factory
from gym_split_planner.domain.enums import Level, Priority, TagEffect

TESTS_DATA = Path(__file__).parent.parent / "data"


@pytest.fixture
def seeded(engine: Engine, session: Session) -> Session:
    assert seed_if_empty(engine) is not None
    return session


def _count(session: Session, model: type[object]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_counts(seeded: Session) -> None:
    expected = {
        MuscleGroup: 8,
        Muscle: 33,
        Equipment: 4,
        Source: 48,
        Tag: 3,
        MovementFamily: 40,
        Exercise: 81,
        StretchExercise: 11,
        DailyRoutineItem: 8,
        SplitTemplate: 6,
        AppSetting: 6,
    }
    assert {model: _count(seeded, model) for model in expected} == expected


def test_seed_runs_only_on_an_empty_database(engine: Engine, seeded: Session) -> None:
    assert seed_if_empty(engine) is None
    assert _count(seeded, Exercise) == 81


def test_seed_skipped_when_plans_exist(engine: Engine, session: Session) -> None:
    session.add(Plan(name="Importata", preferences={}))
    session.commit()

    assert seed_if_empty(engine) is None
    assert _count(session, Exercise) == 0


def test_every_exercise_has_a_primary_muscle(seeded: Session) -> None:
    for exercise in seeded.scalars(select(Exercise)):
        levels = {link.level for link in exercise.muscles}
        assert Level.PRIMARY in levels, exercise.code


def test_family_ranks_are_unique_and_consecutive(seeded: Session) -> None:
    ranks: dict[int, list[int]] = {}
    for exercise in seeded.scalars(select(Exercise)):
        ranks.setdefault(exercise.primary_family_id, []).append(exercise.family_rank)
    for family_ranks in ranks.values():
        assert sorted(family_ranks) == list(range(1, len(family_ranks) + 1))


def test_every_family_has_a_primary_exercise(seeded: Session) -> None:
    used = set(seeded.scalars(select(Exercise.primary_family_id)))
    assert used == set(seeded.scalars(select(MovementFamily.id)))


def test_every_preset_slot_has_a_valid_candidate(seeded: Session) -> None:
    """Ogni slot ha almeno un esercizio attivo della sua famiglia non escluso da un'etichetta."""
    candidates: dict[int, set[str]] = {}
    for exercise in seeded.scalars(select(Exercise).where(Exercise.is_active)):
        if any(link.tag.effect == TagEffect.EXCLUDE for link in exercise.tags):
            continue
        for family_id in (exercise.primary_family_id, exercise.secondary_family_id):
            if family_id is not None:
                candidates.setdefault(family_id, set()).add(exercise.code)
    for slot in seeded.scalars(select(SlotTemplate)):
        assert candidates.get(slot.family_id), (slot.day.split.code, slot.day.code, slot.position)


def test_split_days_per_week(seeded: Session) -> None:
    days = {
        split.code: sum(day.times_per_week for day in split.days)
        for split in seeded.scalars(select(SplitTemplate))
    }
    assert days == {"ppl-3": 3, "ppl-6": 6, "ul-4": 4, "pplul-5": 5, "pp-4": 4, "fb-3": 3}


def test_bands_match_the_research(seeded: Session) -> None:
    bands = Counter(
        (m.priority, m.weekly_min, m.weekly_max) for m in seeded.scalars(select(Muscle))
    )
    assert bands == {
        (Priority.PRIORITY, 10, 18): 10,
        (Priority.STANDARD, 6, 10): 2,
        (Priority.NONE, None, None): 21,
    }


def test_neck_tags(seeded: Session) -> None:
    counts = Counter(
        link.tag.code for exercise in seeded.scalars(select(Exercise)) for link in exercise.tags
    )
    assert counts == {"neck-caution": 26, "neck-tip": 7, "neck-avoid": 1}


def test_golden_files_cover_every_split_and_muscle(seeded: Session) -> None:
    with (TESTS_DATA / "golden_volumes.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    splits = set(seeded.scalars(select(SplitTemplate.code)))
    muscles = set(seeded.scalars(select(Muscle.code)))

    assert {(r["split_code"], r["muscle_code"]) for r in rows} == {
        (s, m) for s in splits for m in muscles
    }
    assert all(float(r["expected"]) * 2 == int(float(r["expected"]) * 2) for r in rows)


def test_invalid_reference_stops_the_seed(tmp_path: Path, engine: Engine) -> None:
    data = tmp_path / "data"
    shutil.copytree(DATA_DIR, data)
    path = data / "exercises.yaml"
    path.write_text(
        path.read_text(encoding="utf-8").replace("family: press-horizontal", "family: refuso", 1),
        encoding="utf-8",
    )

    with (
        make_session_factory(engine)() as session,
        pytest.raises(SeedError, match="famiglia 'refuso' inesistente"),
    ):
        load_seed(session, data)


def test_unknown_field_stops_the_seed(tmp_path: Path, engine: Engine) -> None:
    data = tmp_path / "data"
    shutil.copytree(DATA_DIR, data)
    path = data / "tags.yaml"
    path.write_text(
        path.read_text(encoding="utf-8").replace("  show_badge: true", "  show_badges: true", 1),
        encoding="utf-8",
    )

    with (
        make_session_factory(engine)() as session,
        pytest.raises(SeedError, match=r"tags\.yaml"),
    ):
        load_seed(session, data)
