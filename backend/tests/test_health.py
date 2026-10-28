from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from gym_split_planner import __version__


def test_health_ok(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__, "database": "ok"}


def test_health_database_unreachable(app: FastAPI, client: TestClient) -> None:
    # Un file dentro una cartella inesistente: SQLite non riesce ad aprirlo.
    app.state.engine = create_engine("sqlite:////percorso/inesistente/db.sqlite")

    response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json()["status"] == "error"
    assert response.json()["database"] == "error"
