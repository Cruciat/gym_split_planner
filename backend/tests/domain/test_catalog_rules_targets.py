"""Fasce dei muscoli, regole delle etichette e personalizzazioni lette dalle preferenze."""

from typing import Any

import pytest

from gym_split_planner.domain.catalog_rules import (
    check_band,
    check_tag,
    is_valid_target,
)
from gym_split_planner.domain.enums import Priority, TagEffect
from gym_split_planner.domain.model import MuscleOverride, MuscleTarget, TagOverride
from gym_split_planner.domain.preferences import overrides_from_preferences

# --- Fascia di un muscolo (US-07 CA2) ----------------------------------------------


def test_valid_bands() -> None:
    assert check_band(Priority.PRIORITY, 10, 18) == ()
    assert check_band(Priority.STANDARD, 0, 4) == ()
    assert check_band(Priority.NONE, None, None) == ()


def test_band_is_required_with_a_target() -> None:
    violations = check_band(Priority.STANDARD, None, 10)

    assert [(v.rule, v.field) for v in violations] == [("band-required", "weekly_min")]
    assert [v.field for v in check_band(Priority.PRIORITY, None, None)] == [
        "weekly_min",
        "weekly_max",
    ]


@pytest.mark.parametrize(("low", "high"), [(10, 10), (12, 8)])
def test_band_minimum_below_maximum(low: float, high: float) -> None:
    violations = check_band(Priority.PRIORITY, low, high)

    assert [(v.rule, v.field) for v in violations] == [("band-order", "weekly_max")]


def test_band_is_not_negative() -> None:
    violations = check_band(Priority.PRIORITY, -2, 10)

    assert [(v.rule, v.field) for v in violations] == [("band-negative", "weekly_min")]


def test_no_target_ignores_the_band() -> None:
    """Con "nessun obiettivo" la fascia non conta: il servizio la svuota."""
    assert check_band(Priority.NONE, 12, 8) == ()


@pytest.mark.parametrize(
    ("target", "valid"),
    [
        (MuscleTarget("quads", Priority.STANDARD, 6, 10), True),
        (MuscleTarget("quads", Priority.NONE), True),
        (MuscleTarget("quads", Priority.STANDARD, 8, 6), False),
        (MuscleTarget("quads", Priority.PRIORITY, None, 10), False),
    ],
)
def test_is_valid_target(target: MuscleTarget, valid: bool) -> None:
    assert is_valid_target(target) is valid


# --- Etichette (US-08 CA1) --------------------------------------------------------


def test_bonus_and_penalty_need_points() -> None:
    assert check_tag(TagEffect.PENALTY, 3) == ()
    assert check_tag(TagEffect.NONE, 0) == ()
    assert check_tag(TagEffect.EXCLUDE, 0) == ()
    violations = check_tag(TagEffect.BONUS, 0)
    assert [(v.rule, v.field) for v in violations] == [("points-required", "points")]


# --- Personalizzazioni dalle preferenze (modello dati, § 4.7) -------------------------


def test_overrides_from_preferences() -> None:
    preferences: dict[str, Any] = {
        "version": 2,
        "overrides": {
            "muscles": {"quads": {"weekly_max": 8}, "chest-lower": {"priority": "none"}},
            "tags": {"neck-caution": {"effect": "exclude"}, "favourite": {"points": 2}},
        },
    }

    overrides = overrides_from_preferences(preferences)

    assert overrides.muscles == {
        "quads": MuscleOverride(weekly_max=8),
        "chest-lower": MuscleOverride(priority=Priority.NONE),
    }
    assert overrides.tags == {
        "neck-caution": TagOverride(effect=TagEffect.EXCLUDE),
        "favourite": TagOverride(points=2),
    }


@pytest.mark.parametrize(
    "preferences",
    [
        {},
        {"overrides": None},
        {"overrides": {"muscles": []}},
        {"overrides": {"muscles": {"quads": "alto"}}},
    ],
)
def test_missing_or_malformed_overrides_are_empty(preferences: dict[str, Any]) -> None:
    overrides = overrides_from_preferences(preferences)

    assert dict(overrides.muscles) == {}
    assert dict(overrides.tags) == {}


def test_unknown_values_are_ignored() -> None:
    preferences = {
        "overrides": {
            "muscles": {"quads": {"priority": "altissima", "weekly_min": "sei", "weekly_max": 9}},
            "tags": {"neck-caution": {"effect": "ban", "points": True}},
        }
    }

    overrides = overrides_from_preferences(preferences)

    assert overrides.muscles == {"quads": MuscleOverride(weekly_max=9)}
    assert overrides.tags == {"neck-caution": TagOverride()}
