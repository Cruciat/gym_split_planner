"""Regole di giorni e slot della scheda (modello dati, § 7; API, § 6.8)."""

import pytest

from gym_split_planner.domain.catalog_rules import Violation
from gym_split_planner.domain.enums import Kind, Level
from gym_split_planner.domain.model import Catalog
from gym_split_planner.domain.plan_rules import (
    SlotState,
    check_slot,
    default_prescription,
)
from tests.domain.conftest import EXERCISES, MUSCLES, TAGS, exercise

P = Level.PRIMARY


@pytest.fixture
def catalog() -> Catalog:
    """Il catalogo di prova, con un esercizio di famiglia secondaria e uno disattivato."""
    extra = [
        exercise(
            "converging-press",
            "press-horizontal",
            {"chest-mid": P},
            secondary_family="press-incline",
        ),
        exercise("old-incline", "press-incline", {"chest-upper": P}, rank=9, is_active=False),
    ]
    return Catalog.build([*EXERCISES, *extra], MUSCLES, TAGS)


def _rules(violations: tuple[Violation, ...]) -> list[tuple[str, str | None]]:
    return [(v.rule, v.field) for v in violations]


def _state(**overrides: object) -> SlotState:
    values: dict[str, object] = {
        "family": "press-incline",
        "exercise": "chest-press-incline",
        "second_exercise": None,
        "times_per_week": 2,
        "rep_min": 6,
        "rep_max": 12,
    }
    values.update(overrides)
    return SlotState(**values)  # type: ignore[arg-type]


def test_valid_slot(catalog: Catalog) -> None:
    assert check_slot(_state(), catalog) == ()
    assert check_slot(_state(exercise=None), catalog) == ()


def test_exercise_must_belong_to_the_family(catalog: Catalog) -> None:
    violations = check_slot(_state(exercise="cable-lateral-raise"), catalog)

    assert _rules(violations) == [("exercise-family", "exercise_id")]


def test_secondary_family_is_enough(catalog: Catalog) -> None:
    assert check_slot(_state(exercise="converging-press"), catalog) == ()


def test_inactive_exercise_cannot_be_chosen(catalog: Catalog) -> None:
    violations = check_slot(_state(exercise="old-incline"), catalog, changed={"exercise"})
    kept = check_slot(_state(exercise="old-incline"), catalog, changed=set())
    second = check_slot(_state(second_exercise="old-incline"), catalog, changed={"second_exercise"})

    assert _rules(violations) == [("exercise-inactive", "exercise_id")]
    assert kept == ()
    assert _rules(second) == [("exercise-inactive", "second_exercise_id")]


def test_unknown_exercise(catalog: Catalog) -> None:
    violations = check_slot(_state(exercise="inesistente", second_exercise="altro"), catalog)

    assert _rules(violations) == [
        ("unknown-reference", "exercise_id"),
        ("unknown-reference", "second_exercise_id"),
    ]


def test_second_session_needs_a_repeated_day(catalog: Catalog) -> None:
    violations = check_slot(
        _state(times_per_week=1, second_exercise="cable-lateral-raise"), catalog
    )

    assert _rules(violations) == [("second-session-requires-repeat", "second_exercise_id")]


def test_second_session_can_be_any_family_but_not_the_main_one(catalog: Catalog) -> None:
    other_family = check_slot(_state(second_exercise="cable-lateral-raise"), catalog)
    same = check_slot(_state(second_exercise="chest-press-incline"), catalog)

    assert other_family == ()
    assert _rules(same) == [("second-exercise-distinct", "second_exercise_id")]


def test_reps_order(catalog: Catalog) -> None:
    assert _rules(check_slot(_state(rep_min=12, rep_max=8), catalog)) == [("reps-order", "rep_max")]
    assert check_slot(_state(rep_min=10, rep_max=10), catalog) == ()


@pytest.mark.parametrize(
    ("kind", "expected"),
    [(Kind.COMPOUND, (3, 6, 12)), (Kind.ISOLATION, (3, 10, 15)), (None, (3, 6, 12))],
)
def test_default_prescription(kind: Kind | None, expected: tuple[int, int, int]) -> None:
    assert default_prescription(kind) == expected
