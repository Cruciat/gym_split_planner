"""Preferenze della scheda: lettura e normalizzazione (modello dati, § 4.7; ADR 0014)."""

from typing import Any

import pytest

from gym_split_planner.domain.enums import Priority, TagEffect
from gym_split_planner.domain.model import MuscleOverride, MuscleTarget, TagOverride, TagRule
from gym_split_planner.domain.preferences import (
    DEFAULT_MAX_SESSION_MINUTES,
    default_preferences,
    normalize_preferences,
    plan_preferences,
)

EQUIPMENT = ("machine", "cable", "free-weight", "bodyweight")
MUSCLES = {
    "quads": MuscleTarget("quads", Priority.STANDARD, 6, 10),
    "chest-upper": MuscleTarget("chest-upper", Priority.PRIORITY, 10, 18),
    "chest-lower": MuscleTarget("chest-lower", Priority.NONE),
}
TAGS = {
    "neck-caution": TagRule("neck-caution", TagEffect.PENALTY, 3),
    "neck-avoid": TagRule("neck-avoid", TagEffect.EXCLUDE),
}


def _normalize(raw: dict[str, Any]) -> tuple[dict[str, Any], list[tuple[str, str | None]]]:
    result, violations = normalize_preferences(raw, MUSCLES, TAGS, EQUIPMENT)
    return result, [(v.rule, v.field) for v in violations]


# --- Valori predefiniti e lettura -------------------------------------------------------


def test_default_preferences() -> None:
    assert default_preferences(EQUIPMENT) == {
        "version": 2,
        "equipment_order": list(EQUIPMENT),
        "max_session_minutes": DEFAULT_MAX_SESSION_MINUTES,
        "overrides": {"muscles": {}, "tags": {}},
    }


def test_plan_preferences_reads_the_json() -> None:
    raw = {
        "version": 2,
        "equipment_order": ["free-weight", "machine", "cable", "bodyweight"],
        "max_session_minutes": 60,
        "overrides": {"muscles": {"quads": {"weekly_max": 8}}, "tags": {}},
    }

    prefs = plan_preferences(raw, EQUIPMENT)

    assert prefs.equipment_order == ("free-weight", "machine", "cable", "bodyweight")
    assert prefs.max_session_minutes == 60
    assert prefs.overrides.muscles == {"quads": MuscleOverride(weekly_max=8)}


@pytest.mark.parametrize(
    "raw",
    [
        {},
        {"equipment_order": ["machine"]},
        {"equipment_order": ["machine", "cable", "free-weight", "kettlebell"]},
        {"equipment_order": "machine"},
        {"max_session_minutes": "tanto"},
    ],
)
def test_plan_preferences_falls_back_to_defaults(raw: dict[str, Any]) -> None:
    prefs = plan_preferences(raw, EQUIPMENT)

    assert prefs.equipment_order == EQUIPMENT
    assert prefs.max_session_minutes == DEFAULT_MAX_SESSION_MINUTES


def test_plan_preferences_without_time_limit() -> None:
    assert plan_preferences({"max_session_minutes": None}, EQUIPMENT).max_session_minutes is None


# --- Normalizzazione (regole 1-5 del § 4.7) ------------------------------------------------


def test_overrides_equal_to_the_catalog_are_removed() -> None:
    result, violations = _normalize(
        {
            "equipment_order": list(EQUIPMENT),
            "max_session_minutes": 75,
            "overrides": {
                "muscles": {
                    "quads": {"priority": "standard", "weekly_min": 6, "weekly_max": 8},
                    "chest-upper": {"weekly_min": 10},
                },
                "tags": {"neck-caution": {"effect": "penalty", "points": 3}},
            },
        }
    )

    assert violations == []
    assert result["overrides"] == {"muscles": {"quads": {"weekly_max": 8}}, "tags": {}}


def test_unknown_codes_are_dropped() -> None:
    result, violations = _normalize(
        {
            "equipment_order": list(EQUIPMENT),
            "overrides": {
                "muscles": {"muscolo-eliminato": {"weekly_max": 3}},
                "tags": {"etichetta-eliminata": {"effect": "exclude"}},
            },
        }
    )

    assert violations == []
    assert result["overrides"] == {"muscles": {}, "tags": {}}


def test_effective_band_must_be_valid() -> None:
    _, violations = _normalize(
        {
            "equipment_order": list(EQUIPMENT),
            "overrides": {"muscles": {"quads": {"weekly_min": 12}}},
        }
    )

    assert violations == [("band-order", "overrides.muscles.quads.weekly_max")]


def test_priority_with_target_needs_a_band() -> None:
    _, violations = _normalize(
        {
            "equipment_order": list(EQUIPMENT),
            "overrides": {"muscles": {"chest-lower": {"priority": "priority", "weekly_min": 4}}},
        }
    )

    assert violations == [("band-required", "overrides.muscles.chest-lower.weekly_max")]


def test_no_target_drops_the_band() -> None:
    result, violations = _normalize(
        {
            "equipment_order": list(EQUIPMENT),
            "overrides": {"muscles": {"quads": {"priority": "none", "weekly_min": 3}}},
        }
    )

    assert violations == []
    assert result["overrides"]["muscles"] == {"quads": {"priority": "none"}}


def test_effective_tag_points() -> None:
    ok, ok_violations = _normalize(
        {
            "equipment_order": list(EQUIPMENT),
            "overrides": {"tags": {"neck-avoid": {"effect": "bonus", "points": 2}}},
        }
    )
    _, violations = _normalize(
        {
            "equipment_order": list(EQUIPMENT),
            "overrides": {"tags": {"neck-avoid": {"effect": "penalty"}}},
        }
    )

    assert ok_violations == []
    assert ok["overrides"]["tags"] == {"neck-avoid": {"effect": "bonus", "points": 2}}
    assert violations == [("points-required", "overrides.tags.neck-avoid.points")]


def test_equipment_order_must_be_a_permutation() -> None:
    _, violations = _normalize({"equipment_order": ["machine", "cable", "machine", "bodyweight"]})

    assert violations == [("equipment-order", "equipment_order")]


def test_missing_fields_take_the_defaults() -> None:
    result, violations = _normalize({})

    assert violations == []
    assert result == {
        "version": 2,
        "equipment_order": list(EQUIPMENT),
        "max_session_minutes": DEFAULT_MAX_SESSION_MINUTES,
        "overrides": {"muscles": {}, "tags": {}},
    }


def test_explicit_no_limit_is_kept() -> None:
    result, _ = _normalize({"equipment_order": list(EQUIPMENT), "max_session_minutes": None})

    assert result["max_session_minutes"] is None


def test_tag_override_without_changes_disappears() -> None:
    result, _ = _normalize(
        {"equipment_order": list(EQUIPMENT), "overrides": {"tags": {"neck-caution": {}}}}
    )

    assert result["overrides"]["tags"] == {}


def test_overrides_round_trip_through_plan_preferences() -> None:
    result, _ = _normalize(
        {
            "equipment_order": list(EQUIPMENT),
            "overrides": {"tags": {"neck-caution": {"points": 1}}},
        }
    )

    prefs = plan_preferences(result, EQUIPMENT)

    assert prefs.overrides.tags == {"neck-caution": TagOverride(points=1)}
