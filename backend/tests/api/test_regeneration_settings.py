"""Rigenerazione (US-18; algoritmo G5-G7; API, § 6.9) e impostazioni globali (US-20; § 6.1)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

FREE_WEIGHTS_FIRST = ["free-weight", "bodyweight", "cable", "machine"]


def _create(api: TestClient, split: str = "ppl-6") -> dict[str, Any]:
    splits = {s["code"]: s["id"] for s in api.get("/api/splits").json()}
    plan: dict[str, Any] = api.post("/api/plans", json={"split_id": splits[split]}).json()
    return plan


def _send(api: TestClient, plan: dict[str, Any], method: str, path: str, body: Any = None) -> Any:
    return api.request(
        method,
        f"/api/plans/{plan['id']}{path}",
        json=body,
        headers={"If-Match": f'"{plan["revision"]}"'},
    )


def _ok(api: TestClient, plan: dict[str, Any], method: str, path: str, body: Any = None) -> Any:
    response = _send(api, plan, method, path, body)
    assert response.status_code == 200, response.json()
    return response.json()


def _slot(plan: dict[str, Any], day: str, family: str) -> dict[str, Any]:
    found = next(d for d in plan["days"] if d["name"] == day)
    slot: dict[str, Any] = next(s for s in found["slots"] if s["family"]["code"] == family)
    return slot


def _preview(api: TestClient, plan: dict[str, Any]) -> dict[str, Any]:
    response = api.post(f"/api/plans/{plan['id']}/regenerate/preview")
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    return body


def _prefer_free_weights(api: TestClient, plan: dict[str, Any]) -> dict[str, Any]:
    updated: dict[str, Any] = _ok(
        api, plan, "PUT", "/preferences", {"equipment_order": FREE_WEIGHTS_FIRST}
    )
    return updated


# --- Rigenerazione ---------------------------------------------------------------


def test_g6_nothing_to_regenerate(api: TestClient) -> None:
    plan = _create(api)

    preview = _preview(api, plan)

    assert preview == {"revision": 1, "changes": [], "locked_slots": 0}


def test_preview_after_new_preferences(api: TestClient) -> None:
    plan = _prefer_free_weights(api, _create(api))
    incline = _slot(plan, "Push", "press-incline")

    preview = _preview(api, plan)

    assert preview["revision"] == 2
    change = next(c for c in preview["changes"] if c["slot_id"] == incline["id"])
    assert change["day_name"] == "Push"
    assert change["position"] == 1
    assert change["current"]["name"] == "Chest press inclinata"
    assert change["proposed"]["name"] == "Panca inclinata a 30°"
    assert change["volume_delta"] == []
    # L'anteprima non modifica nulla.
    assert api.get(f"/api/plans/{plan['id']}").json()["revision"] == 2


def test_g5_locked_slots_stay_as_they_are(api: TestClient) -> None:
    plan = _create(api)
    incline = _slot(plan, "Push", "press-incline")
    plan = _ok(api, plan, "PATCH", f"/slots/{incline['id']}", {"locked": True})
    plan = _prefer_free_weights(api, plan)

    preview = _preview(api, plan)
    slot_ids = [c["slot_id"] for c in preview["changes"]]
    plan = _ok(api, plan, "POST", "/regenerate", {"slot_ids": slot_ids})

    assert incline["id"] not in slot_ids
    assert preview["locked_slots"] == 1
    assert _slot(plan, "Push", "press-incline")["exercise"]["code"] == "chest-press-incline"
    assert _preview(api, plan)["changes"] == []


def test_apply_only_the_chosen_slots(api: TestClient) -> None:
    plan = _prefer_free_weights(api, _create(api))
    changes = _preview(api, plan)["changes"]
    assert len(changes) >= 2
    first, *rest = changes

    plan = _ok(api, plan, "POST", "/regenerate", {"slot_ids": [first["slot_id"]]})

    applied = next(s for d in plan["days"] for s in d["slots"] if s["id"] == first["slot_id"])
    assert applied["exercise"]["id"] == first["proposed"]["exercise_id"]
    remaining = {c["slot_id"] for c in _preview(api, plan)["changes"]}
    assert remaining == {c["slot_id"] for c in rest}
    assert plan["revision"] == 3


def test_g7_sets_changed_by_hand_are_kept(api: TestClient) -> None:
    plan = _create(api)
    incline = _slot(plan, "Push", "press-incline")
    plan = _ok(api, plan, "PATCH", f"/slots/{incline['id']}", {"sets": 5, "rep_min": 8})
    plan = _prefer_free_weights(api, plan)

    plan = _ok(api, plan, "POST", "/regenerate", {"slot_ids": [incline["id"]]})

    slot = _slot(plan, "Push", "press-incline")
    assert slot["exercise"]["code"] == "incline-bench-press"
    assert (slot["sets"], slot["rep_min"], slot["rep_max"]) == (5, 8, 12)


def test_second_session_equal_to_the_new_exercise_is_removed(api: TestClient) -> None:
    plan = _create(api)
    incline = _slot(plan, "Push", "press-incline")
    exercises = {e["code"]: e["id"] for e in api.get("/api/catalog").json()["exercises"]}
    plan = _ok(
        api,
        plan,
        "PATCH",
        f"/slots/{incline['id']}",
        {"second_exercise_id": exercises["incline-bench-press"]},
    )
    plan = _prefer_free_weights(api, plan)

    plan = _ok(api, plan, "POST", "/regenerate", {"slot_ids": [incline["id"]]})

    slot = _slot(plan, "Push", "press-incline")
    assert slot["exercise"]["code"] == "incline-bench-press"
    assert slot["second_exercise"] is None


def test_regeneration_needs_the_preview_revision(api: TestClient) -> None:
    plan = _prefer_free_weights(api, _create(api))
    preview = _preview(api, plan)
    ids = [c["slot_id"] for c in preview["changes"]]
    # Nel frattempo un altro dispositivo modifica la scheda.
    _ok(api, plan, "PATCH", "", {"name": "Altro nome"})

    stale = _send(api, plan, "POST", "/regenerate", {"slot_ids": ids})
    missing = api.post(f"/api/plans/{plan['id']}/regenerate", json={"slot_ids": ids})

    assert stale.status_code == 412
    assert stale.json()["current_revision"] == 3
    assert missing.status_code == 428


def test_regeneration_validation(api: TestClient) -> None:
    plan = _create(api)
    other = _create(api, "ppl-3")
    foreign = other["days"][0]["slots"][0]["id"]

    empty = _send(api, plan, "POST", "/regenerate", {"slot_ids": []})
    unknown = _send(api, plan, "POST", "/regenerate", {"slot_ids": [foreign]})

    assert empty.json()["code"] == "validation-error"
    assert unknown.json()["rule"] == "unknown-reference"
    assert api.post("/api/plans/999/regenerate/preview").status_code == 404


# --- Impostazioni globali ---------------------------------------------------------


def test_settings_and_defaults(api: TestClient) -> None:
    settings = api.get("/api/settings").json()
    defaults = api.get("/api/settings/defaults").json()

    assert settings == defaults
    assert settings["level_weights"] == {"P": 1.0, "S": 0.5}
    assert settings["session_cap"] == 10
    assert settings["score_weights"]["equipment"] == 4
    assert settings["duration_params"]["warmup_minutes"] == 10
    assert settings["effort"] == {"rir": "0-2", "failure_last_set": True}
    assert settings["warmup_text"].startswith("5-10 minuti di cardio")


def test_settings_apply_at_once_to_the_analysis(api: TestClient) -> None:
    plan = _create(api)
    push = next(d for d in plan["days"] if d["name"] == "Push")
    minutes = next(s["minutes"] for s in plan["analysis"]["sessions"] if s["day_id"] == push["id"])
    caps = [w for w in plan["analysis"]["warnings"] if w["code"] == "session-cap"]
    settings = api.get("/api/settings").json()
    settings["session_cap"] = 4
    settings["duration_params"]["warmup_minutes"] = 15
    settings["effort"]["rir"] = "1-3"

    response = api.put("/api/settings", json=settings)
    fresh = api.get(f"/api/plans/{plan['id']}").json()

    assert response.status_code == 200
    assert response.json()["session_cap"] == 4
    assert len([w for w in fresh["analysis"]["warnings"] if w["code"] == "session-cap"]) > len(caps)
    new_minutes = next(
        s["minutes"] for s in fresh["analysis"]["sessions"] if s["day_id"] == push["id"]
    )
    assert new_minutes == minutes + 5
    assert fresh["days"][0]["slots"][0]["rir"] == "1-3"
    # Non è una modifica della scheda.
    assert fresh["revision"] == plan["revision"]


def test_score_weights_matter_only_after_regenerating(api: TestClient) -> None:
    plan = _create(api)
    settings = api.get("/api/settings").json()
    settings["score_weights"]["equipment"] = 0

    api.put("/api/settings", json=settings)

    fresh = api.get(f"/api/plans/{plan['id']}").json()
    assert [s["exercise"]["code"] for d in fresh["days"] for s in d["slots"]] == [
        s["exercise"]["code"] for d in plan["days"] for s in d["slots"]
    ]
    assert _preview(api, fresh)["changes"] != []


@pytest.mark.parametrize(
    "change",
    [
        lambda s: s["level_weights"].update(S=2),
        lambda s: s["level_weights"].update(P=0),
        lambda s: s.update(session_cap=0),
        lambda s: s["effort"].update(rir="tanti"),
        lambda s: s["duration_params"].update(set_seconds=-1),
        lambda s: s.update(extra=1),
        lambda s: s.pop("warmup_text"),
    ],
)
def test_invalid_settings(api: TestClient, change: Any) -> None:
    settings = api.get("/api/settings").json()
    change(settings)

    response = api.put("/api/settings", json=settings)

    assert response.status_code == 422
    assert response.json()["code"] == "validation-error"
    assert api.get("/api/settings").json() == api.get("/api/settings/defaults").json()
