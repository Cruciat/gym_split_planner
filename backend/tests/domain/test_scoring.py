"""Punteggio e candidati: casi P1-P12 dell'algoritmo (§ 3.5)."""

import pytest

from gym_split_planner.domain.enums import TagEffect
from gym_split_planner.domain.model import Catalog, Overrides, TagOverride, TagRule
from gym_split_planner.domain.scoring import (
    Preferences,
    ScoreWeights,
    best_candidate,
    candidates,
    equipment_value,
    score_exercise,
)
from tests.domain.conftest import EXERCISES, MUSCLES, exercise

DEFAULT = Preferences()


def _scores(family: str, catalog: Catalog, preferences: Preferences = DEFAULT) -> dict[str, float]:
    return {c.exercise: round(c.score, 2) for c in candidates(family, catalog, preferences)}


def test_p1_example(catalog: Catalog) -> None:
    assert _scores("press-incline", catalog) == {
        "chest-press-incline": 7.9,
        "incline-bench-press": 2.38,
    }


def test_p1_breakdown_sums_to_score(catalog: Catalog) -> None:
    candidate = candidates("press-incline", catalog, DEFAULT)[1]
    b = candidate.breakdown

    assert (b.confidence, b.equipment, b.stretch, b.family, b.rank, b.tags) == pytest.approx(
        (1.8, 4 / 3, 1.0, 1.0, 0.25, -3.0)
    )
    assert b.total == pytest.approx(candidate.score)


def test_p2_avoid_is_excluded(catalog: Catalog) -> None:
    [candidate] = candidates("crunch", catalog, DEFAULT)

    assert candidate.excluded_by == ("neck-avoid",)
    assert best_candidate("crunch", catalog, DEFAULT) is None


def test_p3_plan_can_exclude_caution(catalog: Catalog) -> None:
    preferences = Preferences(
        overrides=Overrides(tags={"neck-caution": TagOverride(effect=TagEffect.EXCLUDE)})
    )

    ordered = candidates("press-incline", catalog, preferences)

    assert [(c.exercise, c.excluded_by) for c in ordered] == [
        ("chest-press-incline", ()),
        ("incline-bench-press", ("neck-caution",)),
    ]


@pytest.mark.parametrize(
    ("order", "expected"),
    [
        (
            ("free-weight", "bodyweight", "cable", "machine"),
            {"incline-bench-press": 5.05, "chest-press-incline": 3.9},
        ),
        (
            ("free-weight", "cable", "machine", "bodyweight"),
            {"chest-press-incline": 5.23, "incline-bench-press": 5.05},
        ),
    ],
)
def test_p4_equipment_order(
    catalog: Catalog, order: tuple[str, ...], expected: dict[str, float]
) -> None:
    scores = _scores("press-incline", catalog, Preferences(equipment_order=order))

    assert scores == expected
    assert list(scores) == list(expected)


def test_p5_tie_broken_by_rank_then_code() -> None:
    a = exercise("b-second", "fam", {"chest-upper": "P"}, rank=2)  # type: ignore[dict-item]
    b = exercise("a-first", "fam", {"chest-upper": "P"}, rank=2)  # type: ignore[dict-item]
    c = exercise("z-rank-one", "fam", {"chest-upper": "P"}, rank=1)  # type: ignore[dict-item]
    catalog = Catalog.build([a, b, c], MUSCLES)
    weights = ScoreWeights(rank=0)

    assert [x.exercise for x in candidates("fam", catalog, DEFAULT, weights)] == [
        "z-rank-one",
        "a-first",
        "b-second",
    ]


def test_p6_weights_change_the_score(catalog: Catalog) -> None:
    weights = ScoreWeights(confidence=0, equipment=0, stretch=0, family=0, rank=0)

    scores = {c.exercise: c.score for c in candidates("press-incline", catalog, DEFAULT, weights)}

    assert scores == {"chest-press-incline": 0.0, "incline-bench-press": -3.0}


def test_p7_secondary_family_counts_half(catalog: Catalog) -> None:
    by_code = {c.exercise: c for c in candidates("triceps-pushdown", catalog, DEFAULT)}

    assert by_code["machine-shoulder-press"].family_match == 0.5
    assert by_code["machine-shoulder-press"].breakdown.family == 0.5


def test_p8_penalties_add_up() -> None:
    double = exercise("double", "fam", {}, tags=frozenset({"a", "b"}))
    catalog = Catalog.build(
        [double], MUSCLES, [TagRule("a", TagEffect.PENALTY, 3), TagRule("b", TagEffect.PENALTY, 3)]
    )

    assert score_exercise(double, 1, catalog, DEFAULT, ScoreWeights()).breakdown.tags == -6


def test_p9_bonus_and_p10_none() -> None:
    liked = exercise("liked", "fam", {}, tags=frozenset({"fav", "info"}))
    catalog = Catalog.build(
        [liked], MUSCLES, [TagRule("fav", TagEffect.BONUS, 2), TagRule("info", TagEffect.NONE)]
    )

    assert score_exercise(liked, 1, catalog, DEFAULT, ScoreWeights()).breakdown.tags == 2


def test_p11_plan_overrides_points(catalog: Catalog) -> None:
    preferences = Preferences(overrides=Overrides(tags={"neck-caution": TagOverride(points=1)}))

    assert _scores("press-incline", catalog, preferences)["incline-bench-press"] == 4.38


def test_inactive_exercises_are_not_candidates() -> None:
    catalog = Catalog.build(
        [exercise("old", "fam", {}, is_active=False), exercise("new", "fam", {})], MUSCLES
    )

    assert [c.exercise for c in candidates("fam", catalog, DEFAULT)] == ["new"]


def test_unknown_tag_is_ignored() -> None:
    odd = exercise("odd", "fam", {}, tags=frozenset({"deleted-tag"}))
    catalog = Catalog.build([odd], MUSCLES)

    assert candidates("fam", catalog, DEFAULT)[0].breakdown.tags == 0


@pytest.mark.parametrize(
    ("equipment", "order", "expected"),
    [
        ("machine", ("machine",), 1.0),
        ("cable", ("machine", "cable"), 0.0),
        ("x", ("machine",), 0.0),
    ],
)
def test_equipment_value_edges(equipment: str, order: tuple[str, ...], expected: float) -> None:
    assert equipment_value(equipment, order) == expected


def test_fixture_is_consistent() -> None:
    assert len({e.code for e in EXERCISES}) == len(EXERCISES)
