"""Fixture condivise: ogni test ha il suo database SQLite in una cartella temporanea."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from gym_split_planner.app import create_app
from gym_split_planner.config import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(database_url=f"sqlite:///{tmp_path / 'data' / 'test.db'}")


@pytest.fixture
def app(settings: Settings) -> Iterator[FastAPI]:
    application = create_app(settings)
    yield application
    application.state.engine.dispose()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
