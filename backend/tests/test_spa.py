"""Distribuzione del frontend con ritorno a index.html (ADR 0009)."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gym_split_planner.app import create_app
from gym_split_planner.config import Settings


@pytest.fixture
def static_dir(tmp_path: Path) -> Path:
    root = tmp_path / "static"
    (root / "assets").mkdir(parents=True)
    (root / "index.html").write_text("<!doctype html><title>app</title>")
    (root / "assets" / "app.js").write_text("console.log('app')")
    (tmp_path / "segreto.txt").write_text("non servire")
    return root


@pytest.fixture
def spa_client(tmp_path: Path, static_dir: Path) -> Iterator[TestClient]:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'db.sqlite'}",
        static_dir=static_dir,
        backup_enabled=False,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        yield client
    app.state.engine.dispose()


def test_root_serves_index(spa_client: TestClient) -> None:
    response = spa_client.get("/")

    assert response.status_code == 200
    assert "<title>app</title>" in response.text
    assert response.headers["cache-control"] == "no-cache"


def test_client_route_serves_index(spa_client: TestClient) -> None:
    response = spa_client.get("/schede/3/preferenze")

    assert response.status_code == 200
    assert "<title>app</title>" in response.text


def test_existing_file_is_served(spa_client: TestClient) -> None:
    response = spa_client.get("/assets/app.js")

    assert response.status_code == 200
    assert response.text == "console.log('app')"


def test_api_paths_are_not_swallowed(spa_client: TestClient) -> None:
    assert spa_client.get("/api/health").json()["status"] == "ok"
    response = spa_client.get("/api/non-esiste")
    assert response.status_code == 404
    assert response.json()["code"] == "not-found"


def test_path_traversal_is_not_served(spa_client: TestClient) -> None:
    response = spa_client.get("/..%2Fsegreto.txt")

    assert "non servire" not in response.text


def test_without_frontend_only_api_is_served(client: TestClient) -> None:
    assert client.get("/").status_code == 404
