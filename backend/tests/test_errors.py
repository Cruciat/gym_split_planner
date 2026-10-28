"""Formato degli errori: Problem Details (contratto delle API, § 3)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from gym_split_planner.api.errors import PROBLEM_JSON, ApiProblem


def test_unknown_api_path_is_not_found(client: TestClient) -> None:
    response = client.get("/api/non-esiste")

    assert response.status_code == 404
    assert response.headers["content-type"] == PROBLEM_JSON
    body = response.json()
    assert body["code"] == "not-found"
    assert body["status"] == 404
    assert body["title"] == "Risorsa non trovata"
    assert "detail" not in body


def test_validation_error_lists_fields(app: FastAPI, client: TestClient) -> None:
    @app.get("/api/_test/sets")
    def sets(count: int) -> dict[str, int]:
        return {"count": count}

    response = client.get("/api/_test/sets", params={"count": "tre"})

    assert response.status_code == 422
    assert response.headers["content-type"] == PROBLEM_JSON
    body = response.json()
    assert body["code"] == "validation-error"
    assert body["errors"][0]["loc"] == ["query", "count"]


def test_api_problem_carries_extra_fields(app: FastAPI, client: TestClient) -> None:
    @app.patch("/api/_test/plan")
    def plan() -> None:
        raise ApiProblem(
            412,
            "revision-mismatch",
            "Revisione non aggiornata",
            "La scheda è stata modificata da un altro dispositivo.",
            current_revision=18,
        )

    response = client.patch("/api/_test/plan")

    assert response.status_code == 412
    assert response.json() == {
        "type": "about:blank",
        "title": "Revisione non aggiornata",
        "status": 412,
        "code": "revision-mismatch",
        "detail": "La scheda è stata modificata da un altro dispositivo.",
        "current_revision": 18,
    }


def test_unexpected_error_hides_details(app: FastAPI, client: TestClient) -> None:
    @app.get("/api/_test/boom")
    def boom() -> None:
        raise RuntimeError("segreto interno")

    response = client.get("/api/_test/boom")

    assert response.status_code == 500
    assert response.headers["content-type"] == PROBLEM_JSON
    assert response.json()["code"] == "internal-error"
    assert "segreto" not in response.text


def test_method_not_allowed(client: TestClient) -> None:
    response = client.post("/api/health")

    assert response.status_code == 405
    assert response.json()["code"] == "method-not-allowed"


def test_other_http_errors_keep_their_detail(app: FastAPI, client: TestClient) -> None:
    @app.get("/api/_test/teapot")
    def teapot() -> None:
        from fastapi import HTTPException

        raise HTTPException(status_code=418, detail="Sono una teiera")

    response = client.get("/api/_test/teapot")

    assert response.status_code == 418
    assert response.json()["code"] == "http-error"
    assert response.json()["detail"] == "Sono una teiera"
