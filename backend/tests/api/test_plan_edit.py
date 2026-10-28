"""Preferenze, giorni, slot e candidati di una scheda (API, § 6.6-6.8, § 8.1; C1-C4)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

EQUIPMENT = ["machine", "cable", "free-weight", "bodyweight"]


class Editor:
    """Scheda di prova: ricorda la revisione e la passa in ``If-Match``."""

    def __init__(self, api: TestClient, plan: dict[str, Any]) -> None:
        self.api = api
        self.plan = plan

    @property
    def url(self) -> str:
        return f"/api/plans/{self.plan['id']}"

    def send(self, method: str, path: str, body: Any = None, *, revision: int | None = None) -> Any:
        rev = self.plan["revision"] if revision is None else revision
        response = self.api.request(
            method, self.url + path, json=body, headers={"If-Match": f'"{rev}"'}
        )
        if response.status_code == 200:
            self.plan = response.json()
            assert response.headers["ETag"] == f'"{self.plan["revision"]}"'
        return response

    def ok(self, method: str, path: str, body: Any = None) -> dict[str, Any]:
        before = self.plan["revision"]
        response = self.send(method, path, body)
        assert response.status_code == 200, response.json()
        assert self.plan["revision"] == before + 1
        return self.plan

    def day(self, name: str) -> dict[str, Any]:
        day: dict[str, Any] = next(d for d in self.plan["days"] if d["name"] == name)
        return day

    def slot(self, day: str, family: str) -> dict[str, Any]:
        slot: dict[str, Any] = next(
            s for s in self.day(day)["slots"] if s["family"]["code"] == family
        )
        return slot

    def volume(self, code: str) -> float:
        value: float = next(
            v["volume"] for v in self.plan["analysis"]["volumes"] if v["code"] == code
        )
        return value


def _ids(api: TestClient, key: str) -> dict[str, int]:
    return {item["code"]: item["id"] for item in api.get("/api/catalog").json()[key]}


def _create(api: TestClient, split: str | None) -> Editor:
    splits = {s["code"]: s["id"] for s in api.get("/api/splits").json()}
    response = api.post("/api/plans", json={"split_id": splits[split] if split else None})
    assert response.status_code == 201
    return Editor(api, response.json())


@pytest.fixture
def ppl6(api: TestClient) -> Editor:
    return _create(api, "ppl-6")


@pytest.fixture
def ppl3(api: TestClient) -> Editor:
    return _create(api, "ppl-3")


def _rules(response: Any) -> list[tuple[str, str | None]]:
    return [(v["rule"], v["field"]) for v in response.json()["violations"]]


# --- Preferenze e personalizzazioni (§ 6.6, § 8.1) ---------------------------------


def test_settings_view(ppl6: Editor) -> None:
    ppl6.ok(
        "PUT",
        "/preferences",
        {
            "equipment_order": EQUIPMENT,
            "max_session_minutes": 60,
            "overrides": {
                "muscles": {"quads": {"weekly_max": 8}},
                "tags": {"neck-caution": {"points": 1}},
            },
        },
    )

    settings = ppl6.api.get(f"{ppl6.url}/settings").json()

    assert settings["revision"] == 2
    assert settings["name"] == ppl6.plan["name"]
    assert settings["equipment_order"] == EQUIPMENT
    assert settings["max_session_minutes"] == 60
    quads = next(m for m in settings["muscles"] if m["code"] == "quads")
    assert quads["catalog"] == {"priority": "standard", "weekly_min": 6, "weekly_max": 10}
    assert quads["override"] == {"priority": None, "weekly_min": None, "weekly_max": 8}
    assert quads["effective"] == {"priority": "standard", "weekly_min": 6, "weekly_max": 8}
    assert quads["group_code"] == "legs"
    caution = next(t for t in settings["tags"] if t["code"] == "neck-caution")
    assert caution["catalog"] == {"effect": "penalty", "points": 3}
    assert caution["override"] == {"effect": None, "points": 1}
    assert caution["effective"] == {"effect": "penalty", "points": 1}
    assert len(settings["muscles"]) == 33
    assert ppl6.api.get("/api/plans/999/settings").status_code == 404


def test_preferences_update_only_the_analysis(ppl6: Editor) -> None:
    exercises = [s["exercise"]["code"] for d in ppl6.plan["days"] for s in d["slots"]]

    plan = ppl6.ok(
        "PUT",
        "/preferences",
        {
            "equipment_order": ["free-weight", "bodyweight", "cable", "machine"],
            "overrides": {"muscles": {"quads": {"weekly_max": 8}}},
        },
    )

    # Le preferenze non rigenerano: gli esercizi restano quelli (US-11, API § 6.6).
    assert [s["exercise"]["code"] for d in plan["days"] for s in d["slots"]] == exercises
    quads = next(v for v in plan["analysis"]["volumes"] if v["code"] == "quads")
    assert (quads["weekly_max"], quads["overridden"], quads["status"]) == (8, True, "above")
    assert plan["preferences"]["equipment_order"][0] == "free-weight"


def test_restore_the_catalog_value(ppl6: Editor) -> None:
    body: dict[str, Any] = {
        "equipment_order": EQUIPMENT,
        "overrides": {"muscles": {"quads": {"weekly_max": 8}}},
    }
    ppl6.ok("PUT", "/preferences", body)

    body["overrides"] = {"muscles": {}}
    plan = ppl6.ok("PUT", "/preferences", body)

    assert plan["preferences"]["overrides"]["muscles"] == {}
    quads = next(v for v in plan["analysis"]["volumes"] if v["code"] == "quads")
    assert (quads["weekly_max"], quads["overridden"]) == (10, False)


def test_invalid_preferences(ppl6: Editor) -> None:
    response = ppl6.send(
        "PUT",
        "/preferences",
        {"equipment_order": EQUIPMENT, "overrides": {"muscles": {"quads": {"weekly_min": 11}}}},
    )

    assert response.status_code == 422
    assert _rules(response) == [("band-order", "overrides.muscles.quads.weekly_max")]
    assert ppl6.api.get(ppl6.url).json()["revision"] == 1


def test_c1_c2_preferences_need_the_revision(ppl6: Editor) -> None:
    body = {"equipment_order": EQUIPMENT}

    missing = ppl6.api.put(f"{ppl6.url}/preferences", json=body)
    ppl6.ok("PUT", "/preferences", body)
    stale = ppl6.send("PUT", "/preferences", body, revision=1)

    assert missing.status_code == 428
    assert stale.status_code == 412
    assert stale.json()["current_revision"] == 2


# --- Giorni (§ 6.7; US-21) --------------------------------------------------------


def test_add_days(api: TestClient) -> None:
    editor = _create(api, None)

    editor.ok("POST", "/days", {"name": "Full body A", "times_per_week": 1})
    plan = editor.ok("POST", "/days", {"name": "Riscaldamento", "times_per_week": 2, "position": 1})

    assert [(d["name"], d["position"], d["times_per_week"]) for d in plan["days"]] == [
        ("Riscaldamento", 1, 2),
        ("Full body A", 2, 1),
    ]
    assert plan["days"][0]["slots"] == []
    assert plan["days"][0]["stretches"] == []


def test_patch_day(ppl3: Editor) -> None:
    push = ppl3.day("Push")

    plan = ppl3.ok("PATCH", f"/days/{push['id']}", {"name": "Spinta", "times_per_week": 2})

    day = next(d for d in plan["days"] if d["id"] == push["id"])
    assert (day["name"], day["times_per_week"]) == ("Spinta", 2)
    # Il giorno ripetuto due volte raddoppia il volume del petto alto.
    assert ppl3.volume("chest-upper") == 12
    assert ppl3.send("PATCH", f"/days/{push['id']}", {"name": None}).status_code == 422
    assert ppl3.send("PATCH", f"/days/{push['id']}", {"times_per_week": 4}).status_code == 422


def test_once_a_week_drops_the_second_session_variants(ppl6: Editor) -> None:
    push = ppl6.day("Push")
    slot = push["slots"][0]
    kickback = _ids(ppl6.api, "exercises")["cable-kickback"]
    ppl6.ok("PATCH", f"/slots/{slot['id']}", {"second_exercise_id": kickback})
    assert len([s for s in ppl6.plan["analysis"]["sessions"] if s["day_id"] == push["id"]]) == 2

    plan = ppl6.ok("PATCH", f"/days/{push['id']}", {"times_per_week": 1})

    assert ppl6.slot("Push", "press-incline")["second_exercise"] is None
    assert len([s for s in plan["analysis"]["sessions"] if s["day_id"] == push["id"]]) == 1


def test_delete_and_reorder_days(ppl6: Editor) -> None:
    push, pull, legs = (d["id"] for d in ppl6.plan["days"])

    plan = ppl6.ok("PUT", "/days/order", {"day_ids": [legs, push, pull]})
    assert [(d["id"], d["position"]) for d in plan["days"]] == [(legs, 1), (push, 2), (pull, 3)]

    plan = ppl6.ok("DELETE", f"/days/{push}")
    assert [(d["id"], d["position"]) for d in plan["days"]] == [(legs, 1), (pull, 2)]
    assert ppl6.volume("chest-upper") == 0


def test_day_order_must_list_every_day(ppl6: Editor) -> None:
    push, pull, legs = (d["id"] for d in ppl6.plan["days"])

    for ids in ([push, pull], [push, pull, legs, legs], [push, pull, 999]):
        response = ppl6.send("PUT", "/days/order", {"day_ids": ids})
        assert _rules(response) == [("order-mismatch", "day_ids")]


def test_c4_day_of_another_plan(api: TestClient, ppl6: Editor) -> None:
    other = _create(api, "ppl-3")
    foreign = other.plan["days"][0]["id"]

    response = ppl6.send("PATCH", f"/days/{foreign}", {"name": "X"})

    assert response.status_code == 404
    assert response.json()["code"] == "not-found"
    assert ppl6.send("DELETE", f"/days/{foreign}").status_code == 404
    assert ppl6.send("POST", f"/days/{foreign}/slots", {"family_id": 1}).status_code == 404


# --- Slot (§ 6.8; US-14 → US-17) --------------------------------------------------


def test_add_slot_with_the_best_candidate_and_defaults(api: TestClient) -> None:
    editor = _create(api, None)
    editor.ok("POST", "/days", {"name": "Braccia", "times_per_week": 1})
    day = editor.plan["days"][0]["id"]
    families = _ids(api, "families")

    editor.ok("POST", f"/days/{day}/slots", {"family_id": families["triceps-pushdown"]})
    plan = editor.ok(
        "POST",
        f"/days/{day}/slots",
        {"family_id": families["press-incline"], "sets": 4, "position": 1},
    )

    slots = plan["days"][0]["slots"]
    assert [(s["position"], s["exercise"]["code"]) for s in slots] == [
        (1, "chest-press-incline"),
        (2, "pushdown-bar"),
    ]
    assert (slots[0]["sets"], slots[0]["rep_min"], slots[0]["rep_max"]) == (4, 6, 12)
    assert (slots[1]["sets"], slots[1]["rep_min"], slots[1]["rep_max"]) == (3, 10, 15)
    assert not slots[0]["locked"]


def test_add_slot_rules(ppl6: Editor) -> None:
    push = ppl6.day("Push")["id"]
    families = _ids(ppl6.api, "families")
    exercises = _ids(ppl6.api, "exercises")

    wrong = ppl6.send(
        "POST",
        f"/days/{push}/slots",
        {"family_id": families["press-incline"], "exercise_id": exercises["cable-kickback"]},
    )
    unknown = ppl6.send("POST", f"/days/{push}/slots", {"family_id": 999})

    assert _rules(wrong) == [("exercise-family", "exercise_id")]
    assert _rules(unknown) == [("unknown-reference", "family_id")]


def test_choose_a_variant(ppl6: Editor) -> None:
    slot = ppl6.slot("Push", "triceps-pushdown")
    assert slot["exercise"]["code"] == "pushdown-bar"
    before = ppl6.volume("triceps-long")
    kickback = _ids(ppl6.api, "exercises")["cable-kickback"]

    ppl6.ok("PATCH", f"/slots/{slot['id']}", {"exercise_id": kickback})

    # Algoritmo, A1: da S a P sul capo lungo, 2 serie, due volte a settimana: +2.
    assert ppl6.volume("triceps-long") == before + 2
    assert ppl6.slot("Push", "triceps-pushdown")["exercise"]["code"] == "cable-kickback"


def test_variant_rules(ppl6: Editor) -> None:
    slot = ppl6.slot("Push", "triceps-pushdown")
    exercises = _ids(ppl6.api, "exercises")

    other_family = ppl6.send("PATCH", f"/slots/{slot['id']}", {"exercise_id": exercises["dip"]})
    unknown = ppl6.send("PATCH", f"/slots/{slot['id']}", {"exercise_id": 9999})
    nulled = ppl6.send("PATCH", f"/slots/{slot['id']}", {"exercise_id": None})

    assert _rules(other_family) == [("exercise-family", "exercise_id")]
    assert _rules(unknown) == [("unknown-reference", "exercise_id")]
    assert nulled.json()["code"] == "validation-error"


def test_inactive_exercise_cannot_be_chosen(ppl6: Editor) -> None:
    exercises = _ids(ppl6.api, "exercises")
    rope = ppl6.api.get(f"/api/exercises/{exercises['pushdown-rope']}").json()
    body = {
        k: rope[k]
        for k in [
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
            "muscles",
            "tags",
        ]
    }
    ppl6.api.put(
        f"/api/exercises/{rope['id']}",
        json={**body, "is_active": False, "source_ids": [s["id"] for s in rope["sources"]]},
    )
    slot = ppl6.slot("Push", "triceps-pushdown")

    response = ppl6.send("PATCH", f"/slots/{slot['id']}", {"exercise_id": rope["id"]})

    assert _rules(response) == [("exercise-inactive", "exercise_id")]


def test_change_family(ppl6: Editor) -> None:
    slot = ppl6.slot("Push", "triceps-pushdown")
    families = _ids(ppl6.api, "families")
    ppl6.ok("PATCH", f"/slots/{slot['id']}", {"sets": 4, "rep_min": 8})

    plan = ppl6.ok("PATCH", f"/slots/{slot['id']}", {"family_id": families["press-incline"]})

    changed = next(s for d in plan["days"] for s in d["slots"] if s["id"] == slot["id"])
    assert changed["family"]["code"] == "press-incline"
    assert changed["exercise"]["code"] == "chest-press-incline"
    assert (changed["sets"], changed["rep_min"], changed["rep_max"]) == (4, 8, 15)


def test_second_session_variant(ppl6: Editor) -> None:
    slot = ppl6.slot("Push", "triceps-pushdown")
    exercises = _ids(ppl6.api, "exercises")
    before = ppl6.volume("triceps-long")

    ppl6.ok("PATCH", f"/slots/{slot['id']}", {"second_exercise_id": exercises["cable-kickback"]})

    # Algoritmo, V4: una seduta su due con il kickback, 2 serie: +1 sul capo lungo.
    assert ppl6.volume("triceps-long") == before + 1
    push = ppl6.day("Push")["id"]
    assert [s["session"] for s in ppl6.plan["analysis"]["sessions"] if s["day_id"] == push] == [
        1,
        2,
    ]
    # Qualunque famiglia va bene per la seconda seduta (US-17 CA1).
    ppl6.ok("PATCH", f"/slots/{slot['id']}", {"second_exercise_id": exercises["dip"]})
    plan = ppl6.ok("PATCH", f"/slots/{slot['id']}", {"second_exercise_id": None})
    assert ppl6.slot("Push", "triceps-pushdown")["second_exercise"] is None
    assert plan["revision"] == 4


def test_second_session_rules(ppl3: Editor, ppl6: Editor) -> None:
    exercises = _ids(ppl6.api, "exercises")
    once = ppl3.slot("Push", "triceps-pushdown")
    twice = ppl6.slot("Push", "triceps-pushdown")

    not_repeated = ppl3.send(
        "PATCH", f"/slots/{once['id']}", {"second_exercise_id": exercises["cable-kickback"]}
    )
    same = ppl6.send(
        "PATCH", f"/slots/{twice['id']}", {"second_exercise_id": exercises["pushdown-bar"]}
    )

    assert _rules(not_repeated) == [("second-session-requires-repeat", "second_exercise_id")]
    assert _rules(same) == [("second-exercise-distinct", "second_exercise_id")]


def test_sets_reps_flags_and_note(ppl6: Editor) -> None:
    slot = ppl6.slot("Pull", "shrug")
    upper_traps = ppl6.volume("traps-upper")

    plan = ppl6.ok(
        "PATCH",
        f"/slots/{slot['id']}",
        {
            "sets": 3,
            "rep_min": 8,
            "rep_max": 10,
            "weekly_weight": 1,
            "locked": True,
            "note": "  Pesante  ",
        },
    )

    changed = next(s for d in plan["days"] for s in d["slots"] if s["id"] == slot["id"])
    assert (changed["sets"], changed["rep_min"], changed["rep_max"]) == (3, 8, 10)
    assert (changed["weekly_weight"], changed["locked"], changed["note"]) == (1, True, "Pesante")
    assert ppl6.volume("traps-upper") > upper_traps

    ppl6.ok("PATCH", f"/slots/{slot['id']}", {"is_optional": True, "note": ""})
    assert ppl6.slot("Pull", "shrug")["note"] is None
    assert ppl6.volume("traps-upper") < upper_traps


@pytest.mark.parametrize(
    ("body", "code"),
    [
        ({"rep_min": 15, "rep_max": 8}, "rule-violation"),
        ({"rep_min": 16}, "rule-violation"),
        ({"weekly_weight": 0.7}, "validation-error"),
        ({"sets": 9}, "validation-error"),
        ({"locked": None}, "validation-error"),
        ({"colore": "rosso"}, "validation-error"),
    ],
)
def test_slot_patch_validation(ppl6: Editor, body: dict[str, Any], code: str) -> None:
    slot = ppl6.slot("Push", "triceps-pushdown")  # 10-15 ripetizioni

    response = ppl6.send("PATCH", f"/slots/{slot['id']}", body)

    assert response.json()["code"] == code
    assert ppl6.api.get(ppl6.url).json()["revision"] == 1


def test_locked_slot_can_still_be_edited(ppl6: Editor) -> None:
    slot = ppl6.slot("Push", "triceps-pushdown")
    ppl6.ok("PATCH", f"/slots/{slot['id']}", {"locked": True})

    ppl6.ok("PATCH", f"/slots/{slot['id']}", {"sets": 4})

    assert ppl6.slot("Push", "triceps-pushdown")["sets"] == 4


def test_all_or_nothing(ppl6: Editor) -> None:
    slot = ppl6.slot("Push", "triceps-pushdown")
    exercises = _ids(ppl6.api, "exercises")

    response = ppl6.send(
        "PATCH", f"/slots/{slot['id']}", {"sets": 4, "exercise_id": exercises["dip"]}
    )

    assert response.status_code == 422
    fresh = ppl6.api.get(ppl6.url).json()
    assert fresh["revision"] == 1
    kept = next(s for d in fresh["days"] for s in d["slots"] if s["id"] == slot["id"])
    assert kept["sets"] == slot["sets"]


def test_delete_and_reorder_slots(ppl6: Editor) -> None:
    push = ppl6.day("Push")
    ids = [s["id"] for s in push["slots"]]

    plan = ppl6.ok("PUT", f"/days/{push['id']}/slots/order", {"slot_ids": list(reversed(ids))})
    day = next(d for d in plan["days"] if d["id"] == push["id"])
    assert [s["id"] for s in day["slots"]] == list(reversed(ids))
    assert [s["position"] for s in day["slots"]] == list(range(1, len(ids) + 1))

    plan = ppl6.ok("DELETE", f"/slots/{ids[-1]}")
    day = next(d for d in plan["days"] if d["id"] == push["id"])
    assert [s["id"] for s in day["slots"]] == list(reversed(ids[:-1]))
    assert [s["position"] for s in day["slots"]] == list(range(1, len(ids)))

    mismatch = ppl6.send("PUT", f"/days/{push['id']}/slots/order", {"slot_ids": ids})
    assert _rules(mismatch) == [("order-mismatch", "slot_ids")]


def test_c4_slot_of_another_plan(api: TestClient, ppl6: Editor) -> None:
    other = _create(api, "ppl-3")
    foreign = other.plan["days"][0]["slots"][0]["id"]

    assert ppl6.send("PATCH", f"/slots/{foreign}", {"sets": 2}).status_code == 404
    assert ppl6.send("DELETE", f"/slots/{foreign}").status_code == 404
    assert api.get(f"{ppl6.url}/slots/{foreign}/candidates").status_code == 404


def test_c3_every_change_returns_the_full_plan(ppl6: Editor) -> None:
    slot = ppl6.slot("Push", "triceps-pushdown")

    response = ppl6.send("PATCH", f"/slots/{slot['id']}", {"locked": True})

    assert set(response.json()) >= {"id", "revision", "days", "analysis", "preferences"}
    assert response.headers["ETag"] == '"2"'


# --- Candidati (§ 6.8; algoritmo, § 5) -------------------------------------------------


def test_candidates_for_the_main_exercise(ppl6: Editor) -> None:
    slot = ppl6.slot("Push", "triceps-pushdown")

    body = ppl6.api.get(f"{ppl6.url}/slots/{slot['id']}/candidates").json()

    assert body["slot_id"] == slot["id"]
    assert body["session"] == 1
    assert body["current_exercise_id"] == slot["exercise"]["id"]
    codes = [c["code"] for c in body["candidates"]]
    assert codes[0] == "pushdown-bar"
    assert {"pushdown-rope", "cable-kickback"} <= set(codes)
    kickback = next(c for c in body["candidates"] if c["code"] == "cable-kickback")
    assert kickback["family_match"] == "primary"
    assert kickback["equipment"] == "cable"
    assert [(d["code"], d["delta"]) for d in kickback["volume_delta"]] == [("triceps-long", 2.0)]
    breakdown = kickback["score_breakdown"]
    assert sum(breakdown.values()) == pytest.approx(kickback["score"], abs=0.01)
    rope = next(c for c in body["candidates"] if c["code"] == "pushdown-rope")
    assert rope["volume_delta"] == []


def test_excluded_candidates_come_last(ppl6: Editor) -> None:
    slot = ppl6.slot("Legs", "crunch")

    candidates = ppl6.api.get(f"{ppl6.url}/slots/{slot['id']}/candidates").json()["candidates"]

    assert candidates[-1]["code"] == "floor-crunch"
    assert candidates[-1]["excluded_by"] == ["neck-avoid"]
    assert candidates[-1]["badges"][0]["code"] == "neck-avoid"
    assert all(not c["excluded_by"] for c in candidates[:-1])


def test_candidates_for_the_second_session(ppl3: Editor, ppl6: Editor) -> None:
    slot = ppl6.slot("Push", "triceps-pushdown")

    body = ppl6.api.get(f"{ppl6.url}/slots/{slot['id']}/candidates", params={"session": 2}).json()
    once = ppl3.slot("Push", "triceps-pushdown")
    refused = ppl3.api.get(f"{ppl3.url}/slots/{once['id']}/candidates", params={"session": 2})
    invalid = ppl6.api.get(f"{ppl6.url}/slots/{slot['id']}/candidates", params={"session": 3})

    assert body["session"] == 2
    assert body["current_exercise_id"] is None
    matches = [c["family_match"] for c in body["candidates"]]
    assert matches[:3] == ["primary", "primary", "primary"]
    assert "other" in matches
    assert matches.index("other") > 2
    kickback = next(c for c in body["candidates"] if c["code"] == "cable-kickback")
    # Una seduta su due: metà dell'effetto della prima seduta (algoritmo, § 5).
    assert [(d["code"], d["delta"]) for d in kickback["volume_delta"]] == [("triceps-long", 1.0)]
    assert _rules(refused) == [("second-session-requires-repeat", "session")]
    assert invalid.json()["code"] == "validation-error"
