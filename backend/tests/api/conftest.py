"""Test di integrazione dell'API (API, § 9): database temporaneo con i dati iniziali.

Il database con migrazioni e seed si prepara una volta per sessione di test e si
copia per ogni test: ogni test parte dagli stessi dati e può modificarli liberamente.
"""

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from gym_split_planner.app import create_app
from gym_split_planner.config import Settings
from gym_split_planner.db.engine import make_engine
from gym_split_planner.db.migrate import upgrade_to_head
from gym_split_planner.db.seed.loader import seed_if_empty


@pytest.fixture(scope="session")
def seeded_database(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("seed") / "seeded.db"
    engine = make_engine(f"sqlite:///{path}")
    upgrade_to_head(engine)
    assert seed_if_empty(engine) is not None
    engine.dispose()
    return path


@pytest.fixture
def api_app(seeded_database: Path, tmp_path: Path) -> Iterator[FastAPI]:
    database = tmp_path / "api.db"
    shutil.copyfile(seeded_database, database)
    application = create_app(Settings(database_url=f"sqlite:///{database}", backup_enabled=False))
    yield application
    application.state.engine.dispose()


@pytest.fixture
def api(api_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(api_app, raise_server_exceptions=False) as test_client:
        yield test_client
