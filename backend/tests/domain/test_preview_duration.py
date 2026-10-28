"""Anteprima delle varianti (A1-A6), durata (D1-D4) e analisi della scheda (§ 5, 6, 8)."""

from dataclasses import replace

import pytest

from gym_split_planner.domain.analysis import AnalysisSettings, PlanWarning, analyze
from gym_split_planner.domain.duration import DurationParams, day_minutes
from gym_split_planner.domain.enums import BandStatus, Priority
from gym_split_planner.domain.model import (
    Catalog,
    Day,
    MuscleOverride,
    Overrides,
    PlanShape,
    Slot,
)
from gym_split_planner.domain.preview import variant_previews
from gym_split_planner.domain.scoring import Preferences
from tests.domain.conftest import push_day

DEFAULT = Preferences()


def _deltas(
    day: Day, position: int, catalog: Catalog, session: int = 1
) -> dict[str, dict[str, float]]:
    return {
        p.candidate.exercise: p.volume_delta
        for p in variant_previews(day, position, catalog, DEFAULT, session=session)
    }


def test_a1_kickback_instead_of_pushdown(catalog: Catalog) -> None:
    deltas = _deltas(push_day(2), 6, catalog)

    assert deltas["cable-kickback"] == {"triceps-long": 2.0}


def test_a2_same_map_no_difference(catalog: Catalog) -> None:
    assert _deltas(push_day(2), 6, catalog)["pushdown-bar"] == {}


def test_a3_second_session_halves_the_occurrences(catalog: Catalog) -> None:
    day = push_day(2)
    slots = list(day.slots)
    slots[5] = replace(slots[5], second_exercise="cable-kickback")
    day = replace(day, slots=tuple(slots))

    assert _deltas(day, 6, catalog)["cable-kickback"] == {"triceps-long": 1.0}


def test_a4_excluded_candidates_are_listed_last(catalog: Catalog) -> None:
    day = Day("core", 1, (Slot("crunch", 2, 10, 15),))

    [preview] = variant_previews(day, 1, catalog, DEFAULT)

    assert preview.candidate.excluded_by == ("neck-avoid",)
    assert preview.volume_delta == {"rectus-abdominis": 2.0, "obliques": 1.0}


def test_a6_second_session_from_another_family(catalog: Catalog) -> None:
    day = Day("upper", 2, (Slot("press-horizontal", 3, 6, 12, "chest-press"),))

    previews = variant_previews(day, 1, catalog, DEFAULT, session=2)
    deltas = {p.candidate.exercise: p.volume_delta for p in previews}

    assert previews[0].candidate.exercise == "chest-press"
    assert previews[0].candidate.family_match == 1.0
    assert deltas["cable-fly-seated"] == {"triceps-lateral": -1.5, "triceps-medial": -1.5}
    others = [p.candidate for p in previews[1:]]
    assert all(c.family_match == 0.0 for c in others)


def test_optional_slot_has_no_volume_effect(catalog: Catalog) -> None:
    assert all(not d for d in _deltas(push_day(1), 7, catalog).values())


def test_d1_push_of_the_document(catalog: Catalog) -> None:
    assert day_minutes(push_day(1), catalog) == [pytest.approx(60.5)]


def test_d2_optional_does_not_count(catalog: Catalog) -> None:
    day = push_day(1)
    without = replace(day, slots=day.slots[:-1])

    assert day_minutes(day, catalog) == day_minutes(without, catalog)


def test_d3_one_warmup_per_group(catalog: Catalog) -> None:
    params = DurationParams(warmup_minutes=0, stretching_minutes=0)
    one = Day("d", 1, (Slot("press-incline", 1, 6, 12, "chest-press-incline"),))
    two = Day("d", 1, (*one.slots, Slot("press-horizontal", 1, 6, 12, "chest-press")))

    [single] = day_minutes(one, catalog, params)
    [double] = day_minutes(two, catalog, params)

    # 45 s di serie + 60 s di cambio per esercizio; 180 s di avvicinamento una volta sola.
    assert single * 60 == 45 + 60 + 180
    assert double * 60 == 2 * (45 + 60) + 180


def test_two_sessions_two_durations(catalog: Catalog) -> None:
    day = Day("d", 2, (Slot("triceps-pushdown", 2, 10, 15, "pushdown-bar", "cable-kickback"),))

    assert len(day_minutes(day, catalog)) == 2


def test_d4_and_warnings(catalog: Catalog) -> None:
    plan = PlanShape(
        (
            push_day(1),
            Day("extra", 1, (Slot("crunch", 2, 10, 15),)),
        )
    )
    settings = AnalysisSettings(max_session_minutes=60)

    analysis = analyze(plan, catalog, DEFAULT, settings)

    assert PlanWarning("session-too-long", day="push", session=1, minutes=60.5) in analysis.warnings
    assert PlanWarning("empty-slot", day="extra", position=1, family="crunch") in analysis.warnings
    assert PlanWarning("volume-below", muscle="chest-upper", volume=6) in analysis.warnings
    push = analysis.sessions[0]
    assert (push.day, push.session, push.max_muscle, push.max_volume) == (
        "push",
        1,
        "triceps-lateral",
        8.0,
    )


def test_analysis_uses_effective_targets(catalog: Catalog) -> None:
    overrides = Overrides(muscles={"chest-upper": MuscleOverride(weekly_min=4, weekly_max=8)})

    analysis = analyze(PlanShape((push_day(1),)), catalog, Preferences(overrides=overrides))
    chest = next(v for v in analysis.volumes if v.muscle == "chest-upper")
    lower = next(v for v in analysis.volumes if v.muscle == "chest-lower")

    assert (chest.status, chest.overridden, chest.target.weekly_max) == (BandStatus.WITHIN, True, 8)
    assert (lower.status, lower.target.priority) == (None, Priority.NONE)


def test_session_cap_warning(catalog: Catalog) -> None:
    day = Day(
        "d",
        1,
        (
            Slot("press-incline", 8, 6, 12, "chest-press-incline"),
            Slot("press-incline", 3, 6, 12, "chest-press-incline"),
        ),
    )

    analysis = analyze(
        PlanShape((day,)), catalog, DEFAULT, AnalysisSettings(max_session_minutes=None)
    )

    assert (
        PlanWarning("session-cap", day="d", session=1, muscle="chest-upper", volume=11)
        in analysis.warnings
    )
    assert (
        PlanWarning("volume-above", muscle="triceps-lateral", volume=5.5) not in analysis.warnings
    )
