"""Motore dei PDF e formati del PDF della scheda (ADR 0008; wireframe, § 6)."""

from datetime import date
from typing import get_args

import pytest

from gym_split_planner.api.schemas.catalog import TagSymbol
from gym_split_planner.pdf.render import icon
from gym_split_planner.services.plan_pdf import (
    VolumeGroup,
    VolumeRow,
    filename,
    number,
    rest_text,
    slug,
    two_columns,
)


@pytest.mark.parametrize("symbol", get_args(TagSymbol))
def test_every_tag_symbol_has_an_icon(symbol: str) -> None:
    assert icon(symbol).startswith("<svg")


@pytest.mark.parametrize("name", ["non-esiste", "../templates/plan"])
def test_unknown_or_outside_icon_is_rejected(name: str) -> None:
    with pytest.raises(ValueError, match="Icona sconosciuta"):
        icon(name)


@pytest.mark.parametrize(
    ("seconds", "text"),
    [(None, "—"), (60, "60″"), (90, "90″"), (120, "2′"), (150, "2′30″"), (180, "3′")],
)
def test_rest(seconds: int | None, text: str) -> None:
    assert rest_text(seconds) == text


def test_numbers_in_italian() -> None:
    assert [number(12), number(12.5), number(10.25), number(0)] == ["12", "12,5", "10,25", "0"]


def test_filename() -> None:
    assert slug("PPL 6 giorni — Già fatto!") == "ppl-6-giorni-gia-fatto"
    assert slug("——") == "scheda"
    assert filename("PPL 6 giorni", date(2026, 10, 28)) == "ppl-6-giorni-2026-10-28.pdf"


def test_two_columns_keep_groups_whole() -> None:
    row = VolumeRow("m", "1", "—", "—", False)
    groups = tuple(VolumeGroup(name, (row,) * n) for name, n in [("a", 4), ("b", 3), ("c", 2)])

    left, right = two_columns(groups)

    assert [g.name for g in left] == ["a", "b"]
    assert [g.name for g in right] == ["c"]
    assert two_columns(()) == ((), ())
