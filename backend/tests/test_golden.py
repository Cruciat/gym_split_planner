"""Test di riferimento (algoritmo, § 7; casi G1 e G2).

Genera ogni split predefinito dal database, con le preferenze predefinite, e
confronta il volume settimanale con ``tests/data/golden_volumes.csv``, muscolo per
muscolo e con tolleranza zero. Un valore atteso si cambia solo di proposito, con il
motivo nella descrizione della pull request.
"""

import csv
from collections import defaultdict
from pathlib import Path

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from gym_split_planner.db.engine import make_engine
from gym_split_planner.db.migrate import upgrade_to_head
from gym_split_planner.db.models import SplitTemplate
from gym_split_planner.db.repository import (
    load_catalog,
    load_level_weights,
    load_score_weights,
    load_split_shape,
)
from gym_split_planner.db.seed.loader import seed_if_empty
from gym_split_planner.db.session import make_session_factory
from gym_split_planner.domain.duration import DurationParams, day_minutes
from gym_split_planner.domain.generation import generate
from gym_split_planner.domain.scoring import Preferences
from gym_split_planner.domain.volume import weekly_volume

GOLDEN = Path(__file__).parent / "data" / "golden_volumes.csv"
GOLDEN_DURATIONS = Path(__file__).parent / "data" / "golden_durations.csv"


def _expected() -> dict[str, dict[str, float]]:
    expected: dict[str, dict[str, float]] = defaultdict(dict)
    with GOLDEN.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            expected[row["split_code"]][row["muscle_code"]] = float(row["expected"])
    return expected


@pytest.fixture(scope="module")
def seeded_engine(tmp_path_factory: pytest.TempPathFactory) -> Engine:
    path = tmp_path_factory.mktemp("golden") / "db.sqlite"
    engine = make_engine(f"sqlite:///{path}")
    upgrade_to_head(engine)
    seed_if_empty(engine)
    return engine


@pytest.mark.parametrize("split", sorted(_expected()))
def test_generated_split_matches_golden_volumes(seeded_engine: Engine, split: str) -> None:
    with make_session_factory(seeded_engine)() as session:
        catalog = load_catalog(session)
        shape = load_split_shape(session, split)
        plan, empty = generate(shape, catalog, Preferences(), load_score_weights(session))
        volume = weekly_volume(plan, catalog, load_level_weights(session))

    assert empty == []
    assert volume == _expected()[split]


def test_every_split_has_golden_values(seeded_engine: Engine) -> None:
    with Session(seeded_engine) as session:
        splits = set(session.scalars(select(SplitTemplate.code)))

    assert splits == set(_expected())


def _expected_durations() -> list[tuple[str, str, float]]:
    with GOLDEN_DURATIONS.open(encoding="utf-8") as fh:
        return [
            (r["split_code"], r["day_code"], float(r["expected_minutes"]))
            for r in csv.DictReader(fh)
        ]


@pytest.mark.parametrize(("split", "day", "minutes"), _expected_durations())
def test_generated_day_matches_golden_duration(
    seeded_engine: Engine, split: str, day: str, minutes: float
) -> None:
    with make_session_factory(seeded_engine)() as session:
        catalog = load_catalog(session)
        plan, _ = generate(load_split_shape(session, split), catalog, Preferences())

    [generated] = [d for d in plan.days if d.code == day]
    assert [round(m, 1) for m in day_minutes(generated, catalog, DurationParams())] == [minutes]
