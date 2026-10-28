"""Volume settimanale e valori effettivi: casi V1-V11 dell'algoritmo (§ 2.5)."""

import pytest

from gym_split_planner.domain.enums import BandStatus, Priority, TagEffect
from gym_split_planner.domain.model import (
    Catalog,
    Day,
    LevelWeights,
    MuscleOverride,
    MuscleTarget,
    Overrides,
    PlanShape,
    Slot,
    TagOverride,
    TagRule,
)
from gym_split_planner.domain.volume import (
    band_status,
    effective_targets,
    resolve_muscle,
    resolve_tag,
    session_cap_excesses,
    session_exercises,
    session_volumes,
    weekly_volume,
)
from tests.domain.conftest import push_day


def test_v1_push_once_a_week(catalog: Catalog) -> None:
    volume = weekly_volume(PlanShape((push_day(1),)), catalog)

    assert volume["chest-upper"] == 6
    assert volume["chest-mid"] == 7.5
    assert volume["delt-front"] == 4.5
    assert volume["triceps-long"] == 4


def test_v1_twice_a_week_doubles(catalog: Catalog) -> None:
    volume = weekly_volume(PlanShape((push_day(2),)), catalog)

    assert volume["chest-upper"] == 12
    assert volume["chest-mid"] == 15


def test_v2_optional_slot_does_not_count(catalog: Catalog) -> None:
    volume = weekly_volume(PlanShape((push_day(1),)), catalog)

    # La shoulder press facoltativa darebbe 2 serie P al deltoide anteriore.
    assert volume["delt-front"] == 4.5


def test_v3_alternate_weeks(catalog: Catalog) -> None:
    day = Day("pull", 2, (Slot("shrug", 2, 10, 15, "shrug-dumbbell-machine", weekly_weight=0.5),))

    assert weekly_volume(PlanShape((day,)), catalog)["traps-upper"] == 2


def test_v4_second_session_variant(catalog: Catalog) -> None:
    day = Day("push", 2, (Slot("triceps-pushdown", 2, 10, 15, "pushdown-bar", "cable-kickback"),))

    assert weekly_volume(PlanShape((day,)), catalog)["triceps-long"] == 3


def test_second_session_variant_ignored_on_single_day(catalog: Catalog) -> None:
    day = Day("push", 1, (Slot("triceps-pushdown", 2, 10, 15, "pushdown-bar", "cable-kickback"),))

    assert weekly_volume(PlanShape((day,)), catalog)["triceps-long"] == 1


def test_v5_empty_slot(catalog: Catalog) -> None:
    day = Day("push", 2, (Slot("press-incline", 3, 6, 12),))

    volume = weekly_volume(PlanShape((day,)), catalog)

    assert set(volume) == set(catalog.muscles)
    assert all(value == 0 for value in volume.values())


def test_v6_no_target_no_status() -> None:
    assert band_status(12, MuscleTarget("chest-lower", Priority.NONE)) is None


@pytest.mark.parametrize(
    ("volume", "expected"),
    [
        (9.5, BandStatus.BELOW),
        (10, BandStatus.WITHIN),
        (18, BandStatus.WITHIN),
        (18.5, BandStatus.ABOVE),
    ],
)
def test_v7_band_edges(volume: float, expected: BandStatus) -> None:
    assert band_status(volume, MuscleTarget("chest-upper", Priority.PRIORITY, 10, 18)) is expected


def test_v9_only_max_overridden() -> None:
    target = MuscleTarget("quads", Priority.STANDARD, 6, 10)
    overrides = Overrides(muscles={"quads": MuscleOverride(weekly_max=8)})

    assert resolve_muscle(target, overrides) == MuscleTarget("quads", Priority.STANDARD, 6, 8)


def test_v10_priority_overridden_to_none() -> None:
    target = MuscleTarget("quads", Priority.STANDARD, 6, 10)
    overrides = Overrides(muscles={"quads": MuscleOverride(priority=Priority.NONE)})

    effective = resolve_muscle(target, overrides)

    assert effective == MuscleTarget("quads", Priority.NONE)
    assert band_status(20, effective) is None


def test_v11_override_of_unknown_muscle_is_ignored(catalog: Catalog) -> None:
    overrides = Overrides(muscles={"non-esiste": MuscleOverride(priority=Priority.NONE)})

    targets = effective_targets(catalog, overrides)

    assert targets == dict(catalog.muscles)


def test_muscle_without_override_is_unchanged() -> None:
    target = MuscleTarget("quads", Priority.STANDARD, 6, 10)

    assert resolve_muscle(target, Overrides()) is target


def test_tag_override() -> None:
    rule = TagRule("neck-caution", TagEffect.PENALTY, 3)

    assert resolve_tag(rule, Overrides()) is rule
    assert resolve_tag(rule, Overrides(tags={"neck-caution": TagOverride(points=1)})) == TagRule(
        "neck-caution", TagEffect.PENALTY, 1
    )
    assert resolve_tag(
        rule, Overrides(tags={"neck-caution": TagOverride(effect=TagEffect.EXCLUDE)})
    ) == TagRule("neck-caution", TagEffect.EXCLUDE, 3)


def test_custom_level_weights(catalog: Catalog) -> None:
    volume = weekly_volume(PlanShape((push_day(1),)), catalog, LevelWeights(1.0, 0.0))

    assert volume["chest-upper"] == 3


def test_sessions_of_a_day(catalog: Catalog) -> None:
    single = push_day(2)
    with_variant = Day(
        "push", 2, (Slot("triceps-pushdown", 2, 10, 15, "pushdown-bar", "cable-kickback"),)
    )

    assert len(session_exercises(single)) == 1
    sessions = session_exercises(with_variant)
    assert [[exercise for _, exercise in s] for s in sessions] == [
        ["pushdown-bar"],
        ["cable-kickback"],
    ]
    volumes = session_volumes(with_variant, catalog)
    assert volumes[0]["triceps-long"] == 1
    assert volumes[1]["triceps-long"] == 2


def test_session_cap(catalog: Catalog) -> None:
    day = Day(
        "push",
        1,
        (
            Slot("press-incline", 6, 6, 12, "chest-press-incline"),
            Slot("press-incline", 5, 6, 12, "chest-press-incline"),
        ),
    )

    excesses = session_cap_excesses(PlanShape((day,)), catalog, cap=10)

    assert [(e.muscle, e.volume) for e in excesses] == [("chest-upper", 11)]
    assert session_cap_excesses(PlanShape((push_day(1),)), catalog, cap=10) == []


def test_family_match_and_level_weights(catalog: Catalog) -> None:
    incline = catalog.exercises["chest-press-incline"]

    assert incline.family_match("press-incline") == 1.0
    assert incline.family_match("fly-horizontal") is None
    assert catalog.exercises["machine-shoulder-press"].family_match("triceps-pushdown") == 0.5
    assert LevelWeights().of(None) == 0.0
