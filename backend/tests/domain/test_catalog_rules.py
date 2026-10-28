"""Regole del catalogo: codici generati dal nome e validità di un esercizio (US-03, US-04)."""

import pytest

from gym_split_planner.domain.catalog_rules import (
    Violation,
    check_exercise,
    is_valid_code,
    next_numbered_code,
    slugify,
    unique_code,
)
from gym_split_planner.domain.enums import Level

P, S = Level.PRIMARY, Level.SECONDARY


# --- Codici ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "code"),
    [
        ("Chest press inclinata", "chest-press-inclinata"),
        ("Panca inclinata a 30°", "panca-inclinata-a-30"),
        ("Croci  ai cavi — dal basso!", "croci-ai-cavi-dal-basso"),
        ("Àlzate laterali (un braccio)", "alzate-laterali-un-braccio"),
        ("  Dip  ", "dip"),
        ("Curl dell'avambraccio", "curl-dell-avambraccio"),
    ],
)
def test_slugify(name: str, code: str) -> None:
    assert slugify(name) == code


def test_slugify_without_letters_or_digits_gives_a_fallback() -> None:
    assert slugify("°!?") == "voce"


def test_slugify_is_limited_in_length_without_trailing_dash() -> None:
    code = slugify("a" * 50 + " " + "b" * 50, max_length=55)

    assert len(code) <= 55
    assert not code.endswith("-")


def test_unique_code_adds_a_number_when_taken() -> None:
    assert unique_code("dip", set()) == "dip"
    assert unique_code("dip", {"dip"}) == "dip-2"
    assert unique_code("dip", {"dip", "dip-2", "dip-3"}) == "dip-4"


def test_unique_code_respects_the_maximum_length() -> None:
    base = "x" * 60

    code = unique_code(base, {base}, max_length=60)

    assert code.endswith("-2")
    assert len(code) == 60


@pytest.mark.parametrize(
    ("code", "valid"),
    [
        ("chest-press", True),
        ("src-07", True),
        ("a", True),
        ("Chest", False),
        ("chest--press", False),
        ("-chest", False),
        ("chest-", False),
        ("chest press", False),
        ("", False),
    ],
)
def test_is_valid_code(code: str, valid: bool) -> None:
    assert is_valid_code(code) is valid


def test_next_numbered_code() -> None:
    assert next_numbered_code("src", {"src-01", "src-48", "altro"}) == "src-49"
    assert next_numbered_code("src", set()) == "src-01"
    assert next_numbered_code("src", {"src-99"}) == "src-100"


# --- Esercizio -------------------------------------------------------------------


def test_valid_exercise_has_no_violations() -> None:
    assert check_exercise({"chest-upper": P, "chest-mid": S}, 1, None) == ()
    assert check_exercise({"chest-upper": P}, 1, 2) == ()


def test_exercise_needs_a_primary_muscle() -> None:
    violations = check_exercise({"chest-mid": S}, 1, None)

    assert violations == (
        Violation("primary-muscle-required", "muscles", "Serve almeno un muscolo P."),
    )
    assert check_exercise({}, 1, None)[0].rule == "primary-muscle-required"


def test_secondary_family_must_differ_from_the_primary() -> None:
    violations = check_exercise({"chest-upper": P}, 3, 3)

    assert [v.rule for v in violations] == ["secondary-family-distinct"]
    assert violations[0].field == "secondary_family_id"


def test_all_violations_are_reported_together() -> None:
    violations = check_exercise({"chest-upper": S}, 3, 3)

    assert [v.rule for v in violations] == [
        "primary-muscle-required",
        "secondary-family-distinct",
    ]
