"""Backup giornaliero del database (ADR 0003, NF5)."""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from gym_split_planner.app import create_app
from gym_split_planner.config import Settings
from gym_split_planner.db.backup import (
    backup_name,
    list_backups,
    run_daily_backup,
    sqlite_path,
)
from gym_split_planner.db.engine import make_engine
from gym_split_planner.db.migrate import upgrade_to_head
from gym_split_planner.db.seed.loader import seed_if_empty

TODAY = date(2026, 10, 28)


@pytest.fixture
def database(tmp_path: Path) -> Path:
    path = tmp_path / "data" / "gym_split_planner.db"
    engine = make_engine(f"sqlite:///{path}")
    upgrade_to_head(engine)
    seed_if_empty(engine)
    engine.dispose()
    return path


def _count_exercises(path: Path) -> int:
    connection = sqlite3.connect(path)
    try:
        return int(connection.execute("SELECT count(*) FROM exercise").fetchone()[0])
    finally:
        connection.close()


def test_daily_backup_is_a_usable_copy(database: Path, tmp_path: Path) -> None:
    backups = tmp_path / "backups"

    result = run_daily_backup(database, backups, TODAY, keep=14)

    assert result.created == backups / "gym_split_planner-2026-10-28.db"
    assert _count_exercises(result.created) == 81
    assert not list(backups.glob("*.partial"))


def test_one_backup_per_day(database: Path, tmp_path: Path) -> None:
    backups = tmp_path / "backups"
    run_daily_backup(database, backups, TODAY, keep=14)

    again = run_daily_backup(database, backups, TODAY, keep=14)

    assert again.created is None
    assert len(list_backups(backups)) == 1


def test_rotation_keeps_the_most_recent(database: Path, tmp_path: Path) -> None:
    backups = tmp_path / "backups"
    for offset in range(16, 0, -1):
        run_daily_backup(database, backups, TODAY - timedelta(days=offset), keep=14)

    result = run_daily_backup(database, backups, TODAY, keep=14)

    names = [path.name for path in list_backups(backups)]
    assert len(names) == 14
    assert names[-1] == backup_name(TODAY)
    assert names[0] == backup_name(TODAY - timedelta(days=13))
    assert len(result.removed) == 1


def test_other_files_are_never_removed(database: Path, tmp_path: Path) -> None:
    backups = tmp_path / "backups"
    backups.mkdir()
    (backups / "copia-a-mano.db").write_text("non toccare")

    run_daily_backup(database, backups, TODAY, keep=1)
    run_daily_backup(database, backups, TODAY + timedelta(days=1), keep=1)

    assert (backups / "copia-a-mano.db").exists()
    assert [p.name for p in list_backups(backups)] == [backup_name(TODAY + timedelta(days=1))]


def test_backup_while_the_app_writes(database: Path, tmp_path: Path) -> None:
    engine: Engine = make_engine(f"sqlite:///{database}")
    with engine.begin() as connection:
        connection.execute(text("UPDATE exercise SET notes = 'scritta prima del backup'"))
        result = run_daily_backup(database, tmp_path / "backups", TODAY, keep=14)
    engine.dispose()

    # La transazione non era ancora confermata: il backup contiene lo stato precedente.
    assert result.created is not None
    assert _count_exercises(result.created) == 81


def test_missing_database_creates_nothing(tmp_path: Path) -> None:
    result = run_daily_backup(tmp_path / "manca.db", tmp_path / "backups", TODAY, keep=14)

    assert result.created is None


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("sqlite:////data/gym_split_planner.db", Path("/data/gym_split_planner.db")),
        ("sqlite://", None),
        ("sqlite:///:memory:", None),
        ("postgresql://utente@host/db", None),
    ],
)
def test_sqlite_path(url: str, expected: Path | None) -> None:
    assert sqlite_path(url) == expected


def test_app_creates_the_backup_at_startup(database: Path, tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{database}", backup_check_seconds=3600)
    app = create_app(settings)

    with TestClient(app):
        pass

    assert len(list_backups(database.parent / "backups")) == 1
    app.state.engine.dispose()
