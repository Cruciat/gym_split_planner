"""Creazione, modifica ed eliminazione di esercizi e fonti (API, § 6.3; US-03, US-04, US-05)."""

from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update

from gym_split_planner.db.models import (
    Exercise,
    ExerciseMuscle,
    ExerciseSource,
    MovementFamily,
    Plan,
    PlanDay,
    PlanSlot,
)
from gym_split_planner.db.session import make_session_factory

# --- Aiuti -----------------------------------------------------------------------


def _catalog(api: TestClient) -> dict[str, Any]:
    body: dict[str, Any] = api.get("/api/catalog").json()
    return body


def _ids(api: TestClient) -> dict[str, dict[str, int]]:
    """``code`` → ``id`` per ogni elenco del catalogo."""
    catalog = _catalog(api)
    return {
        key: {item["code"]: item["id"] for item in catalog[key]}
        for key in ("muscles", "families", "equipment", "tags", "sources", "exercises")
    }


def _body(api: TestClient, **overrides: Any) -> dict[str, Any]:
    """Corpo valido di un esercizio nuovo, con i riferimenti del seed."""
    ids = _ids(api)
    body: dict[str, Any] = {
        "name": "Chest press convergente",
        "primary_family_id": ids["families"]["press-horizontal"],
        "secondary_family_id": None,
        "family_rank": 3,
        "equipment_id": ids["equipment"]["machine"],
        "equipment_detail": "  ",
        "kind": "compound",
        "stretch": "medium",
        "stretch_note": None,
        "confidence": "opinion",
        "notes": "Macchina a leve convergenti.",
        "muscles": [
            {"muscle_id": ids["muscles"]["chest-mid"], "level": "P"},
            {"muscle_id": ids["muscles"]["delt-front"], "level": "S", "note": "poco"},
        ],
        "tags": [{"tag_id": ids["tags"]["neck-tip"], "note": "Schiena appoggiata"}],
        "source_ids": [ids["sources"]["src-01"]],
    }
    body.update(overrides)
    return body


def _detail_as_body(detail: dict[str, Any]) -> dict[str, Any]:
    """Il dettaglio riscritto come corpo di ``PUT``: la form invia sempre tutto."""
    keys = [
        "name",
        "primary_family_id",
        "secondary_family_id",
        "family_rank",
        "equipment_id",
        "equipment_detail",
        "kind",
        "stretch",
        "stretch_note",
        "confidence",
        "notes",
        "is_active",
        "muscles",
        "tags",
    ]
    body = {key: detail[key] for key in keys}
    body["source_ids"] = [s["id"] for s in detail["sources"]]
    return body


def _rules(response: Any) -> list[tuple[str, str | None]]:
    return [(v["rule"], v["field"]) for v in response.json()["violations"]]


def _add_plan_using(app: FastAPI, exercise_code: str, *, second: bool = False) -> int:
    """Scheda minima con uno slot che usa l'esercizio (le API delle schede arrivano in M4)."""
    with make_session_factory(app.state.engine)() as session:
        exercise = session.scalars(select(Exercise).where(Exercise.code == exercise_code)).one()
        other = session.scalars(select(Exercise).where(Exercise.code != exercise_code)).first()
        assert other is not None
        plan = Plan(name="PPL autunno", preferences={"version": 2})
        day = PlanDay(name="Push", position=1, times_per_week=2)
        slot = PlanSlot(
            position=1,
            family_id=exercise.primary_family_id,
            exercise_id=other.id if second else exercise.id,
            second_exercise_id=exercise.id if second else None,
            sets=3,
            rep_min=8,
            rep_max=12,
            is_optional=False,
        )
        day.slots.append(slot)
        plan.days.append(day)
        session.add(plan)
        session.commit()
        return plan.id


# --- Creazione -------------------------------------------------------------------


def test_create_exercise(api: TestClient) -> None:
    response = api.post("/api/exercises", json=_body(api))

    assert response.status_code == 201
    detail = response.json()
    assert response.headers["Location"] == f"/api/exercises/{detail['id']}"
    assert detail["code"] == "chest-press-convergente"
    assert detail["equipment_detail"] is None
    assert detail["is_active"] is True
    # In ordine di catalogo: petto medio, poi deltoide anteriore.
    assert [(m["level"], m["note"]) for m in detail["muscles"]] == [("P", None), ("S", "poco")]
    assert detail["tags"][0]["note"] == "Schiena appoggiata"
    assert [s["code"] for s in detail["sources"]] == ["src-01"]
    # Compare subito nel catalogo e tra le varianti della sua famiglia.
    assert "chest-press-convergente" in _ids(api)["exercises"]
    chest_press = _ids(api)["exercises"]["chest-press"]
    variants = api.get(f"/api/exercises/{chest_press}").json()["variants"]
    assert "chest-press-convergente" in [v["code"] for v in variants]


def test_generated_code_never_collides(api: TestClient) -> None:
    # "Dip" diventa "dip", già usato dal dip del seed.
    response = api.post("/api/exercises", json=_body(api, name="Dip"))

    assert response.status_code == 201
    assert response.json()["code"] == "dip-2"


def test_create_with_an_explicit_code(api: TestClient) -> None:
    created = api.post("/api/exercises", json={**_body(api), "code": "my-press"})
    invalid = api.post("/api/exercises", json={**_body(api, name="Altro"), "code": "My Press"})
    taken = api.post("/api/exercises", json={**_body(api, name="Altro 2"), "code": "dip"})

    assert created.json()["code"] == "my-press"
    assert _rules(invalid) == [("invalid-code", "code")]
    assert _rules(taken) == [("code-taken", "code")]


def test_exercise_needs_a_primary_muscle(api: TestClient) -> None:
    body = _body(api)
    body["muscles"] = [{**m, "level": "S"} for m in body["muscles"]]

    response = api.post("/api/exercises", json=body)

    assert response.status_code == 422
    problem = response.json()
    assert response.headers["Content-Type"] == "application/problem+json"
    assert problem["code"] == "rule-violation"
    assert problem["rule"] == "primary-muscle-required"
    assert problem["detail"] == "Serve almeno un muscolo P."
    assert _rules(response) == [("primary-muscle-required", "muscles")]


def test_all_rule_violations_together(api: TestClient) -> None:
    body = _body(api, muscles=[], name="DIP (parallele, assistite o macchina dip)")
    body["secondary_family_id"] = body["primary_family_id"]

    response = api.post("/api/exercises", json=body)

    assert _rules(response) == [
        ("primary-muscle-required", "muscles"),
        ("secondary-family-distinct", "secondary_family_id"),
        ("name-taken", "name"),
    ]


def test_unknown_references_and_duplicates(api: TestClient) -> None:
    body = _body(
        api,
        primary_family_id=9999,
        secondary_family_id=9998,
        equipment_id=9999,
        source_ids=[9999],
    )
    body["muscles"] = [*body["muscles"], {"muscle_id": 9999, "level": "P"}, body["muscles"][0]]
    body["tags"] = [*body["tags"], {"tag_id": 9999}, body["tags"][0]]

    response = api.post("/api/exercises", json=body)

    assert _rules(response) == [
        ("unknown-reference", "primary_family_id"),
        ("unknown-reference", "secondary_family_id"),
        ("unknown-reference", "equipment_id"),
        ("unknown-reference", "muscles"),
        ("unknown-reference", "tags"),
        ("unknown-reference", "source_ids"),
        ("duplicate-muscle", "muscles"),
        ("duplicate-tag", "tags"),
    ]


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": "   "},
        {"family_rank": 0},
        {"kind": "cardio"},
        {"muscles": [{"muscle_id": 1, "level": "X"}]},
    ],
)
def test_malformed_body_is_a_validation_error(api: TestClient, overrides: dict[str, Any]) -> None:
    response = api.post("/api/exercises", json=_body(api, **overrides))

    assert response.status_code == 422
    assert response.json()["code"] == "validation-error"


# --- Modifica --------------------------------------------------------------------


def test_replace_exercise(api_app: FastAPI, api: TestClient) -> None:
    ids = _ids(api)
    dip_id = ids["exercises"]["dip"]
    with make_session_factory(api_app.state.engine)() as session:
        session.execute(
            update(Exercise)
            .where(Exercise.id == dip_id)
            .values(updated_at=datetime(2020, 1, 1, tzinfo=UTC))
        )
        session.commit()
    detail = api.get(f"/api/exercises/{dip_id}").json()
    body = _detail_as_body(detail)
    chest_mid, chest_upper = ids["muscles"]["chest-mid"], ids["muscles"]["chest-upper"]
    body["muscles"] = [
        {"muscle_id": chest_mid, "level": "S", "note": None},
        {"muscle_id": chest_upper, "level": "P", "note": "con busto inclinato"},
        {"muscle_id": ids["muscles"]["triceps-long"], "level": "S", "note": None},
    ]
    body["tags"] = [{"tag_id": ids["tags"]["neck-tip"], "note": "Spalle basse"}]
    body["source_ids"] = [ids["sources"]["src-02"], ids["sources"]["src-02"]]
    body["name"] = "Dip alle parallele"

    response = api.put(f"/api/exercises/{dip_id}", json=body)

    assert response.status_code == 200
    updated = response.json()
    assert updated["code"] == "dip"
    assert updated["name"] == "Dip alle parallele"
    levels = {m["muscle_id"]: (m["level"], m["note"]) for m in updated["muscles"]}
    assert levels == {
        chest_upper: ("P", "con busto inclinato"),
        chest_mid: ("S", None),
        ids["muscles"]["triceps-long"]: ("S", None),
    }
    assert updated["tags"] == [{"tag_id": ids["tags"]["neck-tip"], "note": "Spalle basse"}]
    assert [s["code"] for s in updated["sources"]] == ["src-02"]
    assert updated["updated_at"] != "2020-01-01T00:00:00Z"
    assert api.get(f"/api/exercises/{dip_id}").json() == updated


def test_replace_keeps_the_name_of_the_same_exercise(api: TestClient) -> None:
    dip_id = _ids(api)["exercises"]["dip"]
    body = _detail_as_body(api.get(f"/api/exercises/{dip_id}").json())

    assert api.put(f"/api/exercises/{dip_id}", json=body).status_code == 200


def test_deactivate_hides_from_variants(api: TestClient) -> None:
    ids = _ids(api)["exercises"]
    detail = api.get(f"/api/exercises/{ids['katana-extension']}").json()

    response = api.put(
        f"/api/exercises/{ids['katana-extension']}",
        json={**_detail_as_body(detail), "is_active": False},
    )

    assert response.json()["is_active"] is False
    variants = api.get(f"/api/exercises/{ids['cable-overhead-extension']}").json()["variants"]
    assert "katana-extension" not in [v["code"] for v in variants]


def test_replace_validates_like_create(api: TestClient) -> None:
    dip_id = _ids(api)["exercises"]["dip"]
    body = _detail_as_body(api.get(f"/api/exercises/{dip_id}").json())

    taken = api.put(f"/api/exercises/{dip_id}", json={**body, "name": "Face pull"})
    missing = api.put("/api/exercises/9999", json=body)

    assert _rules(taken) == [("name-taken", "name")]
    assert missing.status_code == 404
    assert missing.json()["code"] == "not-found"


# --- Utilizzi ed eliminazione ----------------------------------------------------


def test_usage_and_delete_of_an_unused_exercise(api_app: FastAPI, api: TestClient) -> None:
    dip_id = _ids(api)["exercises"]["dip"]

    usage = api.get(f"/api/exercises/{dip_id}/usage")
    deleted = api.delete(f"/api/exercises/{dip_id}")

    assert usage.json() == {"plans": []}
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert api.get(f"/api/exercises/{dip_id}").status_code == 404
    with make_session_factory(api_app.state.engine)() as session:
        links = select(func.count()).select_from(ExerciseMuscle)
        assert session.scalar(links.where(ExerciseMuscle.exercise_id == dip_id)) == 0
        sources = select(func.count()).select_from(ExerciseSource)
        assert session.scalar(sources.where(ExerciseSource.exercise_id == dip_id)) == 0


@pytest.mark.parametrize("second", [False, True])
def test_used_exercise_cannot_be_deleted(api_app: FastAPI, api: TestClient, second: bool) -> None:
    plan_id = _add_plan_using(api_app, "dip", second=second)
    dip_id = _ids(api)["exercises"]["dip"]

    usage = api.get(f"/api/exercises/{dip_id}/usage")
    response = api.delete(f"/api/exercises/{dip_id}")

    expected = {"plans": [{"id": plan_id, "name": "PPL autunno", "slots": 1}]}
    assert usage.json() == expected
    assert response.status_code == 409
    problem = response.json()
    assert problem["code"] == "in-use"
    assert problem["usage"] == expected
    assert "«PPL autunno»" in problem["detail"]
    assert api.get(f"/api/exercises/{dip_id}").status_code == 200


def test_usage_and_delete_of_a_missing_exercise(api: TestClient) -> None:
    assert api.get("/api/exercises/9999/usage").status_code == 404
    assert api.delete("/api/exercises/9999").status_code == 404


# --- Fonti -----------------------------------------------------------------------


def test_create_source_continues_the_numbering(api: TestClient) -> None:
    response = api.post(
        "/api/sources",
        json={"title": " Schoenfeld 2010 ", "kind": "Revisione", "url": "https://example.org/s"},
    )

    assert response.status_code == 201
    source = response.json()
    assert source["code"] == "src-49"
    assert source["title"] == "Schoenfeld 2010"
    assert source["reliability"] is None
    assert response.headers["Location"] == f"/api/sources/{source['id']}"
    assert "src-49" in _ids(api)["sources"]


def test_source_url_must_be_a_web_address(api: TestClient) -> None:
    response = api.post(
        "/api/sources", json={"title": "x", "kind": "y", "url": "javascript:alert(1)"}
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation-error"


def test_patch_source(api: TestClient) -> None:
    source_id = _ids(api)["sources"]["src-01"]

    response = api.patch(f"/api/sources/{source_id}", json={"reliability": "Media", "url": ""})
    cleared_title = api.patch(f"/api/sources/{source_id}", json={"title": None})

    assert response.status_code == 200
    assert response.json()["reliability"] == "Media"
    assert response.json()["url"] is None
    assert response.json()["title"] == "Haugen et al. 2023"
    assert cleared_title.status_code == 422


def test_delete_source_removes_its_links(api: TestClient) -> None:
    ids = _ids(api)
    chest_press = ids["exercises"]["chest-press"]
    assert "src-01" in [
        s["code"] for s in api.get(f"/api/exercises/{chest_press}").json()["sources"]
    ]

    response = api.delete(f"/api/sources/{ids['sources']['src-01']}")

    assert response.status_code == 204
    sources = api.get(f"/api/exercises/{chest_press}").json()["sources"]
    assert "src-01" not in [s["code"] for s in sources]


def test_missing_source(api: TestClient) -> None:
    assert api.patch("/api/sources/9999", json={"kind": "x"}).status_code == 404
    assert api.delete("/api/sources/9999").status_code == 404


def test_family_used_by_exercises_is_untouched(api_app: FastAPI, api: TestClient) -> None:
    """Eliminare un esercizio non tocca la sua famiglia."""
    dip_id = _ids(api)["exercises"]["dip"]

    api.delete(f"/api/exercises/{dip_id}")

    with make_session_factory(api_app.state.engine)() as session:
        assert session.scalars(
            select(MovementFamily).where(MovementFamily.code == "dip-decline")
        ).one()
