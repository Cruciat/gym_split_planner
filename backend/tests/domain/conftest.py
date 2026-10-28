"""Catalogo ridotto, con le mappe muscolari dei dati iniziali, per i test del dominio."""

import pytest

from gym_split_planner.domain.enums import Confidence, Kind, Level, Priority, Stretch, TagEffect
from gym_split_planner.domain.model import Catalog, Day, ExerciseInfo, MuscleTarget, Slot, TagRule

P, S = Level.PRIMARY, Level.SECONDARY

GROUPS = {
    "press-incline": "chest",
    "press-horizontal": "chest",
    "fly-horizontal": "chest",
    "raise-lateral": "shoulders",
    "press-vertical": "shoulders",
    "triceps-overhead": "triceps",
    "triceps-pushdown": "triceps",
    "shrug": "back",
    "crunch": "core",
}


def exercise(
    code: str,
    family: str,
    muscles: dict[str, Level],
    *,
    rank: int = 1,
    equipment: str = "machine",
    kind: Kind = Kind.ISOLATION,
    stretch: Stretch = Stretch.MEDIUM,
    confidence: Confidence = Confidence.OPINION,
    secondary_family: str | None = None,
    tags: frozenset[str] = frozenset(),
    is_active: bool = True,
    group: str | None = None,
) -> ExerciseInfo:
    return ExerciseInfo(
        code=code,
        primary_family=family,
        family_rank=rank,
        equipment=equipment,
        kind=kind,
        stretch=stretch,
        confidence=confidence,
        muscles=muscles,
        secondary_family=secondary_family,
        tags=tags,
        is_active=is_active,
        group=group if group is not None else GROUPS.get(family, family),
    )


EXERCISES = [
    exercise(
        "chest-press-incline",
        "press-incline",
        {
            "chest-upper": P,
            "chest-mid": S,
            "delt-front": S,
            "triceps-lateral": S,
            "triceps-medial": S,
        },
        kind=Kind.COMPOUND,
        confidence=Confidence.LIMITED,
    ),
    exercise(
        "incline-bench-press",
        "press-incline",
        {
            "chest-upper": P,
            "chest-mid": S,
            "delt-front": S,
            "triceps-lateral": S,
            "triceps-medial": S,
        },
        rank=2,
        equipment="free-weight",
        kind=Kind.COMPOUND,
        stretch=Stretch.HIGH,
        confidence=Confidence.LIMITED,
        tags=frozenset({"neck-caution"}),
    ),
    exercise(
        "chest-press",
        "press-horizontal",
        {
            "chest-upper": S,
            "chest-mid": P,
            "chest-lower": S,
            "delt-front": S,
            "triceps-lateral": S,
            "triceps-medial": S,
        },
        kind=Kind.COMPOUND,
        confidence=Confidence.SOLID,
    ),
    exercise(
        "cable-fly-seated",
        "fly-horizontal",
        {"chest-upper": S, "chest-mid": P, "chest-lower": S, "delt-front": S},
        equipment="cable",
        stretch=Stretch.HIGH,
    ),
    exercise("cable-lateral-raise", "raise-lateral", {"delt-lateral": P, "traps-upper": S}),
    exercise(
        "cable-overhead-extension",
        "triceps-overhead",
        {"triceps-long": P, "triceps-lateral": P, "triceps-medial": P},
        equipment="cable",
        stretch=Stretch.HIGH,
        confidence=Confidence.LIMITED,
        tags=frozenset({"neck-caution"}),
    ),
    exercise(
        "pushdown-bar",
        "triceps-pushdown",
        {"triceps-long": S, "triceps-lateral": P, "triceps-medial": P},
        equipment="cable",
        stretch=Stretch.LOW,
        confidence=Confidence.LIMITED,
    ),
    exercise(
        "cable-kickback",
        "triceps-pushdown",
        {"triceps-long": P, "triceps-lateral": P, "triceps-medial": P},
        rank=3,
        equipment="cable",
        stretch=Stretch.LOW,
    ),
    exercise(
        "machine-shoulder-press",
        "press-vertical",
        {"delt-front": P, "delt-lateral": S, "traps-upper": S, "triceps-lateral": S},
        kind=Kind.COMPOUND,
        secondary_family="triceps-pushdown",
        tags=frozenset({"neck-caution"}),
    ),
    exercise(
        "shrug-dumbbell-machine",
        "shrug",
        {"traps-upper": P, "traps-mid": S, "forearm-flexors": S},
        confidence=Confidence.LIMITED,
        tags=frozenset({"neck-caution"}),
    ),
    exercise(
        "floor-crunch",
        "crunch",
        {"rectus-abdominis": P, "obliques": S},
        equipment="bodyweight",
        tags=frozenset({"neck-avoid"}),
    ),
]

MUSCLES = [
    MuscleTarget("chest-upper", Priority.PRIORITY, 10, 18),
    MuscleTarget("chest-mid", Priority.PRIORITY, 10, 18),
    MuscleTarget("chest-lower", Priority.NONE),
    MuscleTarget("delt-front", Priority.NONE),
    MuscleTarget("delt-lateral", Priority.PRIORITY, 10, 18),
    MuscleTarget("triceps-long", Priority.PRIORITY, 10, 18),
    MuscleTarget("triceps-lateral", Priority.PRIORITY, 10, 18),
    MuscleTarget("triceps-medial", Priority.PRIORITY, 10, 18),
    MuscleTarget("traps-upper", Priority.NONE),
    MuscleTarget("traps-mid", Priority.PRIORITY, 10, 18),
    MuscleTarget("forearm-flexors", Priority.NONE),
    MuscleTarget("rectus-abdominis", Priority.NONE),
    MuscleTarget("obliques", Priority.NONE),
    MuscleTarget("quads", Priority.STANDARD, 6, 10),
]

TAGS = [
    TagRule("neck-tip", TagEffect.NONE),
    TagRule("neck-caution", TagEffect.PENALTY, 3),
    TagRule("neck-avoid", TagEffect.EXCLUDE),
]


@pytest.fixture
def catalog() -> Catalog:
    return Catalog.build(EXERCISES, MUSCLES, TAGS)


def push_day(times_per_week: int = 1) -> Day:
    """Giorno Push del documento di ricerca."""
    return Day(
        "push",
        times_per_week,
        (
            Slot("press-incline", 3, 6, 12, "chest-press-incline"),
            Slot("press-horizontal", 3, 6, 12, "chest-press"),
            Slot("fly-horizontal", 3, 10, 20, "cable-fly-seated"),
            Slot("raise-lateral", 4, 10, 20, "cable-lateral-raise"),
            Slot("triceps-overhead", 3, 10, 15, "cable-overhead-extension"),
            Slot("triceps-pushdown", 2, 10, 15, "pushdown-bar"),
            Slot("press-vertical", 2, 8, 12, "machine-shoulder-press", optional=True),
        ),
    )
