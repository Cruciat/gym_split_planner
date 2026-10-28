"""Database migrato e sessione per i test dello strato ``db``."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from gym_split_planner.db.engine import make_engine
from gym_split_planner.db.migrate import upgrade_to_head
from gym_split_planner.db.session import make_session_factory


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    engine = make_engine(f"sqlite:///{tmp_path / 'db.sqlite'}")
    upgrade_to_head(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with make_session_factory(engine)() as session:
        yield session
