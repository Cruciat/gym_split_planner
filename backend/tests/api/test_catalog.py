"""``GET /api/catalog`` e ``GET /api/exercises/{id}`` (API, § 6.2; US-01, US-02)."""

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from gym_split_planner.db.models import Exercise
from gym_split_planner.db.session import make_session_factory


def _catalog(api: TestClient) -> dict[str, Any]:
    response = api.get("/api/catalog")
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    return body


def _exercise_id(app: FastAPI, code: str) -> int:
    with make_session_factory(app.state.engine)() as session:
        return session.scalars(select(Exercise.id).where(Exercise.code == code)).one()


def _by_code(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["code"]: item for item in items}


# --- Catalogo in blocco ----------------------------------------------------------


def test_catalog_contains_the_initial_data(api: TestClient) -> None:
    catalog = _catalog(api)

    assert len(catalog["exercises"]) == 81
    assert len(catalog["families"]) == 40
    assert len(catalog["muscles"]) == 33
    assert [t["code"] for t in catalog["tags"]] == ["neck-tip", "neck-caution", "neck-avoid"]
    assert [e["code"] for e in catalog["equipment"]] == [
        "machine",
        "cable",
        "free-weight",
        "bodyweight",
    ]
    assert catalog["muscle_groups"][0]["code"] == "chest"
    assert catalog["sources"]
    assert catalog["stretches"]
    assert catalog["daily_routine"]


def test_catalog_summaries_are_enough_for_the_filters(api: TestClient) -> None:
    catalog = _catalog(api)
    muscles = {m["id"]: m["code"] for m in catalog["muscles"]}
    families = {f["id"]: f["code"] for f in catalog["families"]}
    tags = {t["id"]: t["code"] for t in catalog["tags"]}
    dip = _by_code(catalog["exercises"])["dip"]

    assert families[dip["primary_family_id"]] == "dip-decline"
    assert families[dip["secondary_family_id"]] == "triceps-press"
    assert dip["kind"] in {"compound", "isolation"}
    assert dip["is_active"] is True
    assert {"muscle_id", "level"} == set(dip["muscles"][0])
    assert {muscles[m["muscle_id"]] for m in dip["muscles"] if m["level"] == "P"}
    assert [(tags[t["tag_id"]], t["note"]) for t in dip["tags"]] == [
        ("neck-caution", "Attenzione anche per le spalle")
    ]


def test_catalog_exercises_are_sorted_by_name(api: TestClient) -> None:
    names = [e["name"] for e in _catalog(api)["exercises"]]

    assert names == sorted(names)


def test_catalog_etag_and_not_modified(api: TestClient) -> None:
    first = api.get("/api/catalog")
    etag = first.headers["ETag"]

    again = api.get("/api/catalog", headers={"If-None-Match": etag})
    weak = api.get("/api/catalog", headers={"If-None-Match": f'"altro", W/{etag}'})
    different = api.get("/api/catalog", headers={"If-None-Match": '"altro"'})

    assert etag.startswith('"')
    assert first.headers["Cache-Control"] == "no-cache"
    assert again.status_code == 304
    assert again.content == b""
    assert again.headers["ETag"] == etag
    assert weak.status_code == 304
    assert different.status_code == 200


def test_catalog_etag_changes_with_the_content(api_app: FastAPI, api: TestClient) -> None:
    etag = api.get("/api/catalog").headers["ETag"]
    with make_session_factory(api_app.state.engine)() as session:
        session.execute(update(Exercise).where(Exercise.code == "dip").values(is_active=False))
        session.commit()

    response = api.get("/api/catalog", headers={"If-None-Match": etag})

    assert response.status_code == 200
    assert response.headers["ETag"] != etag
    assert _by_code(response.json()["exercises"])["dip"]["is_active"] is False


# --- Dettaglio -------------------------------------------------------------------


def test_exercise_detail(api_app: FastAPI, api: TestClient) -> None:
    exercise_id = _exercise_id(api_app, "cable-overhead-extension")

    response = api.get(f"/api/exercises/{exercise_id}")

    assert response.status_code == 200
    detail = response.json()
    assert detail["code"] == "cable-overhead-extension"
    assert detail["name"] == "Estensione sopra la testa ai cavi (barra o corda)"
    assert detail["kind"] == "isolation"
    assert {"stretch_note", "notes", "created_at", "updated_at"} <= set(detail)
    assert detail["created_at"].endswith("Z")
    assert all({"muscle_id", "level", "note"} == set(m) for m in detail["muscles"])
    assert detail["sources"]
    assert {"id", "code", "title", "url"} <= set(detail["sources"][0])


def test_exercise_variants_follow_the_family_rank(api_app: FastAPI, api: TestClient) -> None:
    exercise_id = _exercise_id(api_app, "cable-overhead-extension")

    variants = api.get(f"/api/exercises/{exercise_id}").json()["variants"]

    assert [v["code"] for v in variants] == [
        "machine-overhead-extension",
        "dumbbell-overhead-extension",
        "katana-extension",
        "ez-skull-crusher",
    ]
    assert len({v["family_id"] for v in variants}) == 1
    assert variants[-1]["tags"][0]["note"] == "Testa appoggiata"


def test_exercise_variants_include_the_secondary_family(api_app: FastAPI, api: TestClient) -> None:
    back_extension = api.get(f"/api/exercises/{_exercise_id(api_app, 'back-extension')}").json()
    romanian = api.get(f"/api/exercises/{_exercise_id(api_app, 'romanian-deadlift')}").json()

    # La famiglia secondaria della back extension è la principale dello stacco rumeno.
    last = back_extension["variants"][-1]
    assert last["code"] == "romanian-deadlift"
    assert last["family_id"] == back_extension["secondary_family_id"]
    # E viceversa: dalla sua famiglia principale si arriva alla back extension.
    assert "back-extension" in [v["code"] for v in romanian["variants"]]


def test_exercise_variants_skip_inactive_exercises(api_app: FastAPI, api: TestClient) -> None:
    with make_session_factory(api_app.state.engine)() as session:
        session.execute(
            update(Exercise).where(Exercise.code == "katana-extension").values(is_active=False)
        )
        session.commit()

    exercise_id = _exercise_id(api_app, "cable-overhead-extension")
    variants = api.get(f"/api/exercises/{exercise_id}").json()["variants"]

    assert "katana-extension" not in [v["code"] for v in variants]


def test_exercise_not_found(api: TestClient) -> None:
    response = api.get("/api/exercises/99999")

    assert response.status_code == 404
    assert response.headers["Content-Type"] == "application/problem+json"
    assert response.json()["code"] == "not-found"
    assert response.json()["title"] == "Esercizio non trovato"


def test_exercise_id_must_be_an_integer(api: TestClient) -> None:
    response = api.get("/api/exercises/abc")

    assert response.status_code == 422
    assert response.json()["code"] == "validation-error"
