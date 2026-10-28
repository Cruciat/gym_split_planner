"""Famiglie, muscoli ed etichette in scrittura (API, § 6.3; US-06, US-07, US-08)."""

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from gym_split_planner.db.models import Exercise, Plan, PlanDay, PlanSlot
from gym_split_planner.db.session import make_session_factory


def _ids(api: TestClient, key: str) -> dict[str, int]:
    return {item["code"]: item["id"] for item in api.get("/api/catalog").json()[key]}


def _by_code(api: TestClient, key: str, code: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = api.get("/api/catalog").json()[key]
    return next(item for item in items if item["code"] == code)


def _rules(response: Any) -> list[tuple[str, str | None]]:
    return [(v["rule"], v["field"]) for v in response.json()["violations"]]


def _add_plan(
    app: FastAPI,
    name: str = "PPL autunno",
    *,
    overrides: dict[str, Any] | None = None,
    family_code: str | None = None,
) -> int:
    """Scheda con le personalizzazioni indicate e, volendo, uno slot di una famiglia."""
    with make_session_factory(app.state.engine)() as session:
        plan = Plan(
            name=name,
            preferences={"version": 2, "overrides": overrides or {"muscles": {}, "tags": {}}},
        )
        if family_code is not None:
            exercise = session.scalars(
                select(Exercise).where(Exercise.primary_family.has(code=family_code))
            ).first()
            assert exercise is not None
            day = PlanDay(name="Push", position=1, times_per_week=1)
            day.slots.append(
                PlanSlot(
                    position=1,
                    family_id=exercise.primary_family_id,
                    exercise_id=exercise.id,
                    sets=3,
                    rep_min=8,
                    rep_max=12,
                    is_optional=False,
                )
            )
            plan.days.append(day)
        session.add(plan)
        session.commit()
        return plan.id


def _preferences(app: FastAPI, plan_id: int) -> tuple[dict[str, Any], int]:
    with make_session_factory(app.state.engine)() as session:
        plan = session.get(Plan, plan_id)
        assert plan is not None
        return plan.preferences, plan.revision


# --- Famiglie (US-06) ------------------------------------------------------------


def test_create_family(api: TestClient) -> None:
    chest = _ids(api, "muscle_groups")["chest"]

    response = api.post(
        "/api/families",
        json={"name": " Spinta convergente ", "muscle_group_id": chest, "description": ""},
    )

    assert response.status_code == 201
    family = response.json()
    assert family["code"] == "spinta-convergente"
    assert family["name"] == "Spinta convergente"
    assert family["description"] is None
    assert family["sort_order"] == 41
    assert response.headers["Location"] == f"/api/families/{family['id']}"


def test_family_rules(api: TestClient) -> None:
    chest = _ids(api, "muscle_groups")["chest"]

    taken = api.post("/api/families", json={"name": "spinta INCLINATA", "muscle_group_id": chest})
    no_group = api.post("/api/families", json={"name": "Nuova", "muscle_group_id": 999})
    blank = api.post("/api/families", json={"name": "  ", "muscle_group_id": chest})

    assert _rules(taken) == [("name-taken", "name")]
    assert _rules(no_group) == [("unknown-reference", "muscle_group_id")]
    assert blank.json()["code"] == "validation-error"


def test_patch_family(api: TestClient) -> None:
    family_id = _ids(api, "families")["press-incline"]
    back = _ids(api, "muscle_groups")["back"]

    response = api.patch(
        f"/api/families/{family_id}",
        json={"name": "Spinta in alto", "description": "Petto alto", "muscle_group_id": back},
    )
    nulled = api.patch(f"/api/families/{family_id}", json={"name": None})

    assert response.status_code == 200
    assert response.json()["code"] == "press-incline"
    assert response.json()["name"] == "Spinta in alto"
    assert response.json()["muscle_group_id"] == back
    assert nulled.status_code == 422
    assert api.patch("/api/families/999", json={"name": "x"}).status_code == 404


def test_family_in_use_cannot_be_deleted(api_app: FastAPI, api: TestClient) -> None:
    plan_id = _add_plan(api_app, family_code="press-horizontal")
    family_id = _ids(api, "families")["press-horizontal"]

    usage = api.get(f"/api/families/{family_id}/usage")
    response = api.delete(f"/api/families/{family_id}")

    assert usage.status_code == 200
    body = usage.json()
    assert body["exercises"] >= 2
    assert body["split_slots"] >= 1
    assert body["plans"] == [{"id": plan_id, "name": "PPL autunno", "slots": 1}]
    assert response.status_code == 409
    assert response.json()["code"] == "in-use"
    assert response.json()["usage"] == body
    assert "esercizi la hanno come famiglia principale" in response.json()["detail"]


def test_delete_family_used_only_as_secondary(api_app: FastAPI, api: TestClient) -> None:
    chest = _ids(api, "muscle_groups")["chest"]
    family = api.post("/api/families", json={"name": "Prova", "muscle_group_id": chest}).json()
    with make_session_factory(api_app.state.engine)() as session:
        session.execute(
            update(Exercise)
            .where(Exercise.code == "chest-press")
            .values(secondary_family_id=family["id"])
        )
        session.commit()

    usage = api.get(f"/api/families/{family['id']}/usage").json()
    response = api.delete(f"/api/families/{family['id']}")

    assert usage == {"exercises": 0, "secondary_exercises": 1, "split_slots": 0, "plans": []}
    assert response.status_code == 204
    assert _by_code(api, "exercises", "chest-press")["secondary_family_id"] is None
    assert api.get(f"/api/families/{family['id']}/usage").status_code == 404


# --- Muscoli (US-07) -------------------------------------------------------------


def test_patch_muscle(api: TestClient) -> None:
    quads = _ids(api, "muscles")["quads"]

    response = api.patch(
        f"/api/muscles/{quads}",
        json={"priority": "priority", "weekly_min": 8, "weekly_max": 14, "short_name": "Quad"},
    )

    assert response.status_code == 200
    muscle = response.json()
    assert (muscle["priority"], muscle["weekly_min"], muscle["weekly_max"]) == ("priority", 8, 14)
    assert muscle["short_name"] == "Quad"
    assert _by_code(api, "muscles", "quads")["weekly_max"] == 14


def test_no_target_clears_the_band(api: TestClient) -> None:
    quads = _ids(api, "muscles")["quads"]

    response = api.patch(f"/api/muscles/{quads}", json={"priority": "none", "weekly_min": 3})

    assert response.json()["weekly_min"] is None
    assert response.json()["weekly_max"] is None


@pytest.mark.parametrize(
    ("code", "body", "rules"),
    [
        (
            "chest-lower",
            {"priority": "standard"},
            [("band-required", "weekly_min"), ("band-required", "weekly_max")],
        ),
        ("quads", {"weekly_min": 10}, [("band-order", "weekly_max")]),
        ("quads", {"weekly_min": -1}, [("band-negative", "weekly_min")]),
    ],
)
def test_muscle_band_rules(
    api: TestClient, code: str, body: dict[str, Any], rules: list[tuple[str, str]]
) -> None:
    response = api.patch(f"/api/muscles/{_ids(api, 'muscles')[code]}", json=body)

    assert response.status_code == 422
    assert _rules(response) == rules


def test_band_that_breaks_a_plan_is_refused(api_app: FastAPI, api: TestClient) -> None:
    plan_id = _add_plan(api_app, overrides={"muscles": {"quads": {"weekly_max": 8}}})
    _add_plan(api_app, "Senza personalizzazioni")
    quads = _ids(api, "muscles")["quads"]

    refused = api.patch(f"/api/muscles/{quads}", json={"weekly_min": 9})
    accepted = api.patch(f"/api/muscles/{quads}", json={"weekly_min": 7})

    assert refused.status_code == 409
    problem = refused.json()
    assert problem["code"] == "invalid-band"
    assert problem["plans"] == [{"id": plan_id, "name": "PPL autunno"}]
    assert "«PPL autunno»" in problem["detail"]
    assert accepted.status_code == 200
    assert accepted.json()["weekly_min"] == 7


def test_plan_without_target_never_blocks(api_app: FastAPI, api: TestClient) -> None:
    _add_plan(api_app, overrides={"muscles": {"quads": {"priority": "none"}}})
    quads = _ids(api, "muscles")["quads"]

    response = api.patch(f"/api/muscles/{quads}", json={"weekly_min": 1, "weekly_max": 2})

    assert response.status_code == 200


def test_missing_muscle(api: TestClient) -> None:
    assert api.patch("/api/muscles/999", json={"notes": "x"}).status_code == 404


# --- Etichette (US-08) -----------------------------------------------------------


def test_create_tag(api: TestClient) -> None:
    response = api.post(
        "/api/tags",
        json={
            "name": "Preferito",
            "symbol": "star",
            "color": "success",
            "effect": "bonus",
            "points": 2,
        },
    )

    assert response.status_code == 201
    tag = response.json()
    assert tag["code"] == "preferito"
    assert tag["show_badge"] is True
    assert tag["sort_order"] == 4
    assert _by_code(api, "tags", "preferito")["effect"] == "bonus"


def test_tag_rules(api: TestClient) -> None:
    no_points = api.post("/api/tags", json={"name": "Bonus", "symbol": "star", "effect": "bonus"})
    taken = api.post("/api/tags", json={"name": "collo: evitare", "symbol": "ban"})
    bad_symbol = api.post("/api/tags", json={"name": "Altro", "symbol": "skull"})

    assert _rules(no_points) == [("points-required", "points")]
    assert _rules(taken) == [("name-taken", "name")]
    assert bad_symbol.json()["code"] == "validation-error"


def test_patch_tag(api: TestClient) -> None:
    tag_id = _ids(api, "tags")["neck-caution"]

    response = api.patch(f"/api/tags/{tag_id}", json={"effect": "exclude", "show_badge": False})
    to_bonus = api.patch(f"/api/tags/{tag_id}", json={"effect": "bonus", "points": 0})

    assert response.status_code == 200
    assert response.json()["effect"] == "exclude"
    assert response.json()["points"] == 3
    assert response.json()["show_badge"] is False
    assert _rules(to_bonus) == [("points-required", "points")]
    assert api.patch(f"/api/tags/{tag_id}", json={"symbol": None}).status_code == 422


def test_tag_usage_and_delete(api_app: FastAPI, api: TestClient) -> None:
    plan_id = _add_plan(
        api_app,
        overrides={"muscles": {}, "tags": {"neck-caution": {"effect": "exclude"}, "neck-tip": {}}},
    )
    tag_id = _ids(api, "tags")["neck-caution"]

    usage = api.get(f"/api/tags/{tag_id}/usage").json()
    response = api.delete(f"/api/tags/{tag_id}")

    assert usage["exercises"] == 26
    assert usage["plans_with_overrides"] == [{"id": plan_id, "name": "PPL autunno"}]
    assert response.status_code == 204
    assert "neck-caution" not in _ids(api, "tags")
    dip = _by_code(api, "exercises", "dip")
    assert dip["tags"] == []
    preferences, revision = _preferences(api_app, plan_id)
    assert preferences["overrides"]["tags"] == {"neck-tip": {}}
    assert revision == 2


def test_assign_and_unassign(api: TestClient) -> None:
    exercises = _ids(api, "exercises")
    tag_id = _ids(api, "tags")["neck-tip"]
    chosen = [exercises["chest-press"], exercises["dip"], exercises["incline-dumbbell-curl"]]

    assigned = api.post(f"/api/tags/{tag_id}/assign", json={"exercise_ids": chosen, "note": "Ok"})
    kept_note = api.post(f"/api/tags/{tag_id}/assign", json={"exercise_ids": chosen})

    assert assigned.status_code == 200
    before = 7  # neck-tip nei dati iniziali
    assert assigned.json()["exercises"] == before + 2
    notes = {
        e["code"]: [t["note"] for t in e["tags"] if t["tag_id"] == tag_id]
        for e in api.get("/api/catalog").json()["exercises"]
        if e["id"] in chosen
    }
    # Il curl inclinato aveva già l'etichetta: la nota fornita la sostituisce.
    assert notes == {"chest-press": ["Ok"], "dip": ["Ok"], "incline-dumbbell-curl": ["Ok"]}
    assert kept_note.json()["exercises"] == before + 2

    removed = api.post(f"/api/tags/{tag_id}/unassign", json={"exercise_ids": chosen[:2]})

    assert removed.json()["exercises"] == before
    assert _by_code(api, "exercises", "chest-press")["tags"] == []


def test_assign_keeps_existing_note_without_note_field(api: TestClient) -> None:
    exercises = _ids(api, "exercises")
    tag_id = _ids(api, "tags")["neck-tip"]
    curl = exercises["incline-dumbbell-curl"]

    api.post(f"/api/tags/{tag_id}/assign", json={"exercise_ids": [curl]})

    tags = _by_code(api, "exercises", "incline-dumbbell-curl")["tags"]
    assert tags == [{"tag_id": tag_id, "note": "Testa appoggiata"}]


def test_assign_rules(api: TestClient) -> None:
    tag_id = _ids(api, "tags")["neck-tip"]

    unknown = api.post(f"/api/tags/{tag_id}/assign", json={"exercise_ids": [9999]})
    empty = api.post(f"/api/tags/{tag_id}/unassign", json={"exercise_ids": []})
    missing = api.post("/api/tags/999/assign", json={"exercise_ids": [1]})

    assert _rules(unknown) == [("unknown-reference", "exercise_ids")]
    assert empty.json()["code"] == "validation-error"
    assert missing.status_code == 404
