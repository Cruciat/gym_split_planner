"""Generazione e rigenerazione: casi G3-G7 dell'algoritmo (§ 4.4).

G1 e G2 (volumi dei preset uguali all'Excel) sono in ``tests/test_golden.py``,
perché usano il catalogo vero dal database.
"""

from dataclasses import replace

from gym_split_planner.domain.enums import TagEffect
from gym_split_planner.domain.generation import (
    EmptySlot,
    SlotChange,
    apply_changes,
    generate,
    regeneration_changes,
)
from gym_split_planner.domain.model import (
    Catalog,
    Day,
    Overrides,
    PlanShape,
    Slot,
    TagOverride,
)
from gym_split_planner.domain.scoring import Preferences

SHAPE = PlanShape(
    (
        Day(
            "push",
            2,
            (
                Slot("press-incline", 3, 6, 12),
                Slot("triceps-overhead", 3, 10, 15),
                Slot("crunch", 2, 10, 15),
            ),
        ),
    )
)
EXCLUDE_CAUTION = Preferences(
    overrides=Overrides(tags={"neck-caution": TagOverride(effect=TagEffect.EXCLUDE)})
)


def test_generation_picks_the_best(catalog: Catalog) -> None:
    plan, empty = generate(SHAPE, catalog, Preferences())

    assert [s.exercise for s in plan.days[0].slots] == [
        "chest-press-incline",
        "cable-overhead-extension",
        None,
    ]
    assert plan.days[0].slots[0].sets == 3
    assert empty == [EmptySlot("push", 3, "crunch", ("neck-avoid",))]


def test_g3_deterministic(catalog: Catalog) -> None:
    assert generate(SHAPE, catalog, Preferences()) == generate(SHAPE, catalog, Preferences())


def test_g4_family_without_valid_candidates(catalog: Catalog) -> None:
    plan, empty = generate(SHAPE, catalog, EXCLUDE_CAUTION)

    assert plan.days[0].slots[1].exercise is None
    assert EmptySlot("push", 2, "triceps-overhead", ("neck-caution",)) in empty


def test_unknown_family_gives_empty_slot_without_reasons(catalog: Catalog) -> None:
    shape = PlanShape((Day("x", 1, (Slot("non-esiste", 3, 6, 12),)),))

    _, empty = generate(shape, catalog, Preferences())

    assert empty == [EmptySlot("x", 1, "non-esiste", ())]


def test_g5_locked_slot_is_kept(catalog: Catalog) -> None:
    plan, _ = generate(SHAPE, catalog, Preferences())
    slots = plan.days[0].slots
    plan = PlanShape(
        (
            replace(
                plan.days[0],
                slots=(
                    replace(slots[0], exercise="incline-bench-press", locked=True),
                    replace(slots[1], exercise="pushdown-bar"),
                    slots[2],
                ),
            ),
        )
    )

    changes = regeneration_changes(plan, catalog, Preferences())

    assert changes == [SlotChange("push", 2, "pushdown-bar", "cable-overhead-extension")]


def test_g6_nothing_to_change(catalog: Catalog) -> None:
    plan, _ = generate(SHAPE, catalog, Preferences())

    assert regeneration_changes(plan, catalog, Preferences()) == []


def test_g7_manual_sets_survive(catalog: Catalog) -> None:
    plan, _ = generate(SHAPE, catalog, Preferences())
    edited = replace(plan.days[0].slots[0], exercise="incline-bench-press", sets=5)
    plan = PlanShape((replace(plan.days[0], slots=(edited, *plan.days[0].slots[1:])),))

    changes = regeneration_changes(plan, catalog, Preferences())
    applied = apply_changes(plan, changes)

    assert applied.days[0].slots[0].exercise == "chest-press-incline"
    assert applied.days[0].slots[0].sets == 5
