"""Split e schede: creazione, scheda completa, gestione, revisioni (API, § 4, § 6.4, § 6.5, § 7)."""

import csv
import re
import statistics
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

GOLDEN = Path(__file__).parent.parent / "data" / "golden_volumes.csv"
EQUIPMENT = ["machine", "cable", "free-weight", "bodyweight"]


def _golden() -> dict[str, dict[str, float]]:
    expected: dict[str, dict[str, float]] = defaultdict(dict)
    with GOLDEN.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            expected[row["split_code"]][row["muscle_code"]] = float(row["expected"])
    return expected


def _split_id(api: TestClient, code: str) -> int:
    splits: list[dict[str, Any]] = api.get("/api/splits").json()
    split_id: int = next(s["id"] for s in splits if s["code"] == code)
    return split_id


def _create(api: TestClient, code: str | None = "ppl-6", **extra: Any) -> dict[str, Any]:
    split_id = _split_id(api, code) if code else None
    response = api.post("/api/plans", json={"split_id": split_id, **extra})
    assert response.status_code == 201, response.json()
    body: dict[str, Any] = response.json()
    return body


def _slot(plan: dict[str, Any], day: str, family: str) -> dict[str, Any]:
    found = next(d for d in plan["days"] if d["name"] == day)
    slot: dict[str, Any] = next(s for s in found["slots"] if s["family"]["code"] == family)
    return slot


# --- Split predefiniti (§ 6.4) -----------------------------------------------------


def test_splits(api: TestClient) -> None:
    splits = api.get("/api/splits").json()

    assert [s["code"] for s in splits] == ["ppl-3", "ppl-6", "ul-4", "pplul-5", "pp-4", "fb-3"]
    ppl6 = splits[1]
    assert ppl6["days_per_week"] == 6
    assert [(d["name"], d["times_per_week"]) for d in ppl6["days"]] == [
        ("Push", 2),
        ("Pull", 2),
        ("Legs", 2),
    ]
    push = ppl6["days"][0]["slots"]
    assert push[0]["family"]["code"] == "press-incline"
    assert (push[0]["sets"], push[0]["rep_min"], push[0]["rep_max"]) == (3, 6, 12)
    assert push[-1]["is_optional"] is True


# --- Creazione (US-10, US-12) --------------------------------------------------------


def test_create_from_a_split(api: TestClient) -> None:
    response = api.post("/api/plans", json={"split_id": _split_id(api, "ppl-6")})

    assert response.status_code == 201
    plan = response.json()
    assert response.headers["Location"] == f"/api/plans/{plan['id']}"
    assert response.headers["ETag"] == '"1"'
    assert re.fullmatch(r"Push/Pull/Legs, 6 giorni — \d\d/\d\d/\d{4}", plan["name"])
    assert plan["revision"] == 1
    assert plan["is_active"] is False
    assert plan["split"]["code"] == "ppl-6"
    assert plan["preferences"] == {
        "version": 2,
        "equipment_order": EQUIPMENT,
        "max_session_minutes": 75,
        "overrides": {"muscles": {}, "tags": {}},
    }
    assert [d["name"] for d in plan["days"]] == ["Push", "Pull", "Legs"]
    push = plan["days"][0]
    assert push["stretches"][0]["code"] == "pec-doorway"
    assert all(slot["exercise"] is not None for day in plan["days"] for slot in day["slots"])
    assert all(not slot["locked"] for day in plan["days"] for slot in day["slots"])
    first = push["slots"][0]
    assert first["exercise"]["code"] == "chest-press-incline"
    assert (first["rest_seconds"], first["rir"], first["last_set_to_failure"]) == (150, "0-2", True)
    assert _slot(plan, "Push", "press-horizontal")["note"] == (
        "Variante: dip alla macchina per più fascio basso"
    )


def test_badges_in_the_plan(api: TestClient) -> None:
    plan = _create(api, "ppl-6")

    lateral = _slot(plan, "Push", "raise-lateral")["exercise"]
    assert lateral["code"] == "cable-lateral-raise"
    assert lateral["badges"] == [
        {
            "tag_id": lateral["badges"][0]["tag_id"],
            "code": "neck-tip",
            "name": "Collo: accorgimento",
            "symbol": "info",
            "color": "info",
            "note": "Se le spalle non salgono",
        }
    ]


@pytest.mark.parametrize("split", sorted(_golden()))
def test_c9_preset_volumes_match_the_reference(api: TestClient, split: str) -> None:
    plan = _create(api, split)

    volumes = {v["code"]: v["volume"] for v in plan["analysis"]["volumes"]}
    assert volumes == _golden()[split]


def test_analysis_shape(api: TestClient) -> None:
    plan = _create(api, "ppl-6")
    analysis = plan["analysis"]

    assert len(analysis["volumes"]) == 33
    long_head = next(v for v in analysis["volumes"] if v["code"] == "triceps-long")
    assert long_head["group_code"] == "triceps"
    assert (long_head["priority"], long_head["status"], long_head["overridden"]) == (
        "priority",
        "below",
        False,
    )
    days = {d["id"] for d in plan["days"]}
    assert {s["day_id"] for s in analysis["sessions"]} == days
    assert all(s["session"] == 1 for s in analysis["sessions"])
    below = next(w for w in analysis["warnings"] if w["code"] == "volume-below")
    assert below["muscle_id"] is not None
    assert below["weekly_min"] < below["weekly_max"]


def test_create_an_empty_plan(api: TestClient) -> None:
    plan = _create(api, None)

    assert re.fullmatch(r"Scheda vuota — \d\d/\d\d/\d{4}", plan["name"])
    assert plan["split"] is None
    assert plan["days"] == []
    assert all(v["volume"] == 0 for v in plan["analysis"]["volumes"])


def test_create_with_name_and_preferences(api: TestClient) -> None:
    plan = _create(
        api,
        "ppl-3",
        name="La mia scheda",
        preferences={
            "equipment_order": ["free-weight", "bodyweight", "cable", "machine"],
            "max_session_minutes": None,
            "overrides": {
                "muscles": {"quads": {"weekly_max": 8}, "chest-upper": {"weekly_min": 10}},
                "tags": {"neck-caution": {"effect": "penalty", "points": 3}},
            },
        },
    )

    assert plan["name"] == "La mia scheda"
    # Pesi liberi in cima: la panca inclinata supera la chest press (algoritmo, P4).
    assert _slot(plan, "Push", "press-incline")["exercise"]["code"] == "incline-bench-press"
    assert plan["preferences"]["max_session_minutes"] is None
    # Le personalizzazioni uguali al catalogo spariscono (modello dati, § 4.7, regola 1).
    assert plan["preferences"]["overrides"] == {
        "muscles": {"quads": {"weekly_max": 8, "priority": None, "weekly_min": None}},
        "tags": {},
    }
    quads = next(v for v in plan["analysis"]["volumes"] if v["code"] == "quads")
    assert (quads["weekly_min"], quads["weekly_max"], quads["overridden"]) == (6, 8, True)
    assert not [w for w in plan["analysis"]["warnings"] if w["code"] == "session-too-long"]


def test_create_with_invalid_preferences(api: TestClient) -> None:
    response = api.post(
        "/api/plans",
        json={
            "split_id": None,
            "preferences": {
                "equipment_order": ["machine", "machine", "cable", "free-weight"],
                "overrides": {"muscles": {"quads": {"weekly_min": 12}}},
            },
        },
    )

    assert response.status_code == 422
    assert [(v["rule"], v["field"]) for v in response.json()["violations"]] == [
        ("equipment-order", "equipment_order"),
        ("band-order", "overrides.muscles.quads.weekly_max"),
    ]


def test_create_with_unknown_split(api: TestClient) -> None:
    response = api.post("/api/plans", json={"split_id": 999})

    assert response.json()["rule"] == "unknown-reference"


def test_empty_slots_say_why(api: TestClient) -> None:
    plan = _create(
        api,
        "ppl-6",
        preferences={
            "equipment_order": EQUIPMENT,
            "overrides": {"tags": {"neck-caution": {"effect": "exclude"}}},
        },
    )

    shoulder = _slot(plan, "Push", "press-vertical")
    assert shoulder["exercise"] is None
    warning = next(w for w in plan["analysis"]["warnings"] if w["slot_id"] == shoulder["id"])
    assert warning["code"] == "empty-slot"
    assert warning["family_id"] == shoulder["family"]["id"]
    assert warning["excluded_by"] == ["neck-caution"]


# --- Lettura ed elenco (US-13, US-19) ----------------------------------------------


def test_read_and_list(api: TestClient) -> None:
    first = _create(api, "ppl-3", name="Prima")
    second = _create(api, None, name="Seconda")

    read = api.get(f"/api/plans/{first['id']}")
    listed = api.get("/api/plans").json()

    assert read.json() == first
    assert read.headers["ETag"] == '"1"'
    assert [p["name"] for p in listed] == ["Seconda", "Prima"]
    assert listed[1] == {
        "id": first["id"],
        "name": "Prima",
        "split_name": "Push/Pull/Legs, 3 giorni",
        "days_per_week": 3,
        "is_active": False,
        "updated_at": first["updated_at"],
    }
    assert second["id"] != first["id"]
    assert api.get("/api/plans/999").json()["code"] == "not-found"


# --- Revisioni (API, § 4; C1-C3) -----------------------------------------------------


def test_c1_modification_without_if_match(api: TestClient) -> None:
    plan = _create(api, None)

    response = api.patch(f"/api/plans/{plan['id']}", json={"name": "Nuovo nome"})

    assert response.status_code == 428
    assert response.json()["code"] == "revision-required"
    assert api.get(f"/api/plans/{plan['id']}").json()["name"] == plan["name"]


def test_c2_c3_two_changes_with_the_same_revision(api: TestClient) -> None:
    plan = _create(api, None)
    url = f"/api/plans/{plan['id']}"

    first = api.patch(url, json={"name": "Uno"}, headers={"If-Match": '"1"'})
    second = api.patch(url, json={"name": "Due"}, headers={"If-Match": '"1"'})

    assert first.status_code == 200
    assert first.json()["revision"] == 2
    assert first.headers["ETag"] == '"2"'
    assert first.json()["name"] == "Uno"
    assert second.status_code == 412
    assert second.json()["code"] == "revision-mismatch"
    assert second.json()["current_revision"] == 2
    assert api.get(url).json()["name"] == "Uno"


@pytest.mark.parametrize(("header", "status"), [('W/"1"', 200), ("1", 200), ("abc", 412)])
def test_if_match_formats(api: TestClient, header: str, status: int) -> None:
    plan = _create(api, None)

    response = api.patch(
        f"/api/plans/{plan['id']}", json={"name": "Altro"}, headers={"If-Match": header}
    )

    assert response.status_code == status


def test_rename_validates_the_name(api: TestClient) -> None:
    plan = _create(api, None)

    response = api.patch(
        f"/api/plans/{plan['id']}", json={"name": "  "}, headers={"If-Match": '"1"'}
    )

    assert response.json()["code"] == "validation-error"


# --- Gestione (US-19 CA2) ----------------------------------------------------------


def test_delete(api: TestClient) -> None:
    plan = _create(api, "ppl-3")

    response = api.delete(f"/api/plans/{plan['id']}")

    assert response.status_code == 204
    assert api.get(f"/api/plans/{plan['id']}").status_code == 404
    assert api.delete(f"/api/plans/{plan['id']}").status_code == 404


def test_duplicate(api: TestClient) -> None:
    plan = _create(api, "ul-4", name="Upper/Lower")
    api.post(f"/api/plans/{plan['id']}/activate")

    response = api.post(f"/api/plans/{plan['id']}/duplicate")

    assert response.status_code == 201
    copy = response.json()
    assert copy["id"] != plan["id"]
    assert copy["name"] == "Upper/Lower (copia)"
    assert copy["is_active"] is False
    assert copy["revision"] == 1
    assert copy["preferences"] == plan["preferences"]

    def shape(p: dict[str, Any]) -> list[Any]:
        return [
            (d["name"], d["times_per_week"], [s["exercise"]["code"] for s in d["slots"]])
            for d in p["days"]
        ]

    assert shape(copy) == shape(plan)
    assert {d["id"] for d in copy["days"]}.isdisjoint({d["id"] for d in plan["days"]})
    assert copy["analysis"]["volumes"] == plan["analysis"]["volumes"]


def test_only_one_active_plan(api: TestClient) -> None:
    first = _create(api, None, name="Prima")
    second = _create(api, None, name="Seconda")

    api.post(f"/api/plans/{first['id']}/activate")
    response = api.post(f"/api/plans/{second['id']}/activate")

    assert response.json()["is_active"] is True
    assert response.json()["revision"] == 1
    active = {p["name"]: p["is_active"] for p in api.get("/api/plans").json()}
    assert active == {"Prima": False, "Seconda": True}
    assert api.post("/api/plans/999/activate").status_code == 404


# --- Prestazioni (C10) -------------------------------------------------------------


def test_c10_modification_is_fast(api: TestClient) -> None:
    plan = _create(api, "ppl-6")
    url = f"/api/plans/{plan['id']}"
    timings = []
    for revision in range(1, 8):
        start = time.perf_counter()
        response = api.patch(
            url, json={"name": f"Nome {revision}"}, headers={"If-Match": str(revision)}
        )
        timings.append(time.perf_counter() - start)
        assert response.status_code == 200

    # Margine per NF1 (300 ms dal telefono): il server risponde in meno di 100 ms.
    assert statistics.median(timings) < 0.1
