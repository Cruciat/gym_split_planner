"""Motore SQLite e migrazioni (ADR 0003, 0009)."""

from pathlib import Path

from sqlalchemy import text

from gym_split_planner.db.engine import make_engine
from gym_split_planner.db.migrate import current_revision, head_revision, upgrade_to_head


def test_sqlite_pragmas_on_every_connection(tmp_path: Path) -> None:
    engine = make_engine(f"sqlite:///{tmp_path / 'sub' / 'db.sqlite'}")

    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1
        assert connection.execute(text("PRAGMA journal_mode")).scalar() == "wal"
    engine.dispose()


def test_engine_creates_database_folder(tmp_path: Path) -> None:
    engine = make_engine(f"sqlite:///{tmp_path / 'nuova' / 'cartella' / 'db.sqlite'}")
    with engine.connect():
        pass
    engine.dispose()

    assert (tmp_path / "nuova" / "cartella" / "db.sqlite").is_file()


def test_upgrade_to_head_from_empty_database(tmp_path: Path) -> None:
    engine = make_engine(f"sqlite:///{tmp_path / 'db.sqlite'}")
    assert current_revision(engine) is None

    upgrade_to_head(engine)

    assert current_revision(engine) == head_revision()
    engine.dispose()


def test_upgrade_is_idempotent(tmp_path: Path) -> None:
    engine = make_engine(f"sqlite:///{tmp_path / 'db.sqlite'}")

    upgrade_to_head(engine)
    upgrade_to_head(engine)

    assert current_revision(engine) == head_revision()
    engine.dispose()
