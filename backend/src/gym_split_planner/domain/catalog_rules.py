"""Regole del catalogo: codici stabili e validità di un esercizio (modello dati, § 1 e § 7).

Funzioni pure, solo libreria standard (ADR 0005). Il servizio le applica prima di
salvare; i messaggi sono in italiano perché arrivano all'utente così come sono.
"""

import re
import unicodedata
from collections.abc import Hashable, Mapping, Set
from dataclasses import dataclass
from typing import Any

from gym_split_planner.domain.enums import Level, Priority, TagEffect
from gym_split_planner.domain.model import MuscleTarget

_CODE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_NOT_ALNUM = re.compile(r"[^a-z0-9]+")

FALLBACK_CODE = "voce"
"""Codice usato quando un nome non contiene né lettere né cifre."""


def slugify(name: str, *, max_length: int = 60) -> str:
    """Codice dal nome: minuscole senza accenti, parole separate da un trattino.

    ``"Panca inclinata a 30°"`` → ``panca-inclinata-a-30`` (API, § 2: il ``code`` si
    genera dal nome alla creazione e poi non cambia più).
    """
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    code = _NOT_ALNUM.sub("-", ascii_name.lower()).strip("-")
    code = code[:max_length].rstrip("-")
    return code or FALLBACK_CODE


def unique_code(base: str, taken: Set[str], *, max_length: int = 60) -> str:
    """``base`` se libero, altrimenti ``base-2``, ``base-3``… entro ``max_length``."""
    if base not in taken:
        return base
    number = 2
    while True:
        suffix = f"-{number}"
        candidate = base[: max_length - len(suffix)].rstrip("-") + suffix
        if candidate not in taken:
            return candidate
        number += 1


def is_valid_code(code: str) -> bool:
    """Minuscole, cifre e trattini singoli tra le parole (``chest-press``, ``src-07``)."""
    return _CODE.fullmatch(code) is not None


def next_numbered_code(prefix: str, taken: Set[str]) -> str:
    """Il primo numero dopo il più alto già usato: ``src-48`` → ``src-49``.

    Le fonti seguono la numerazione dell'Excel (``src-01`` … ``src-48``): le nuove
    continuano la serie invece di prendere un codice dal titolo.
    """
    pattern = re.compile(rf"{re.escape(prefix)}-(\d+)")
    numbers = [int(m.group(1)) for code in taken if (m := pattern.fullmatch(code))]
    return f"{prefix}-{max(numbers, default=0) + 1:02d}"


@dataclass(frozen=True)
class Violation:
    """Regola violata: ``rule`` stabile per il client, ``field`` per la form."""

    rule: str
    field: str | None
    message: str


def check_exercise(
    muscles: Mapping[Any, Level],
    primary_family: Hashable,
    secondary_family: Hashable | None,
) -> tuple[Violation, ...]:
    """Regole di un esercizio che attraversano più campi (US-03 CA2; modello dati, § 7).

    Muscoli e famiglie si possono indicare per ``id`` o per ``code``: conta solo il
    confronto.

    - almeno un muscolo con livello P;
    - famiglia secondaria, se presente, diversa dalla principale.

    Restituisce tutte le violazioni insieme, così la form le mostra in una volta.
    """
    violations: list[Violation] = []
    if Level.PRIMARY not in muscles.values():
        violations.append(
            Violation("primary-muscle-required", "muscles", "Serve almeno un muscolo P.")
        )
    if secondary_family is not None and secondary_family == primary_family:
        violations.append(
            Violation(
                "secondary-family-distinct",
                "secondary_family_id",
                "La famiglia secondaria deve essere diversa dalla principale.",
            )
        )
    return tuple(violations)


def check_band(
    priority: Priority, weekly_min: float | None, weekly_max: float | None
) -> tuple[Violation, ...]:
    """Fascia di un muscolo (US-07 CA2; modello dati, § 3.2).

    Con un obiettivo (prioritario o non prioritario) servono minimo e massimo, con
    ``0 <= minimo < massimo``. Con "nessun obiettivo" la fascia non conta.
    """
    if priority is Priority.NONE:
        return ()
    violations: list[Violation] = []
    for field, value in (("weekly_min", weekly_min), ("weekly_max", weekly_max)):
        if value is None:
            violations.append(
                Violation(
                    "band-required",
                    field,
                    "Con un obiettivo servono il minimo e il massimo della fascia.",
                )
            )
    if violations or weekly_min is None or weekly_max is None:
        return tuple(violations)
    if weekly_min < 0:
        violations.append(
            Violation("band-negative", "weekly_min", "Il minimo non può essere negativo.")
        )
    elif weekly_min >= weekly_max:
        violations.append(
            Violation("band-order", "weekly_max", "Il massimo deve essere maggiore del minimo.")
        )
    return tuple(violations)


def is_valid_target(target: MuscleTarget) -> bool:
    """Vero se priorità e fascia (del catalogo o effettive) rispettano ``check_band``."""
    return not check_band(target.priority, target.weekly_min, target.weekly_max)


def check_tag(effect: TagEffect, points: float) -> tuple[Violation, ...]:
    """Bonus e penalità hanno bisogno di punti positivi (modello dati, § 3.9)."""
    if effect in (TagEffect.BONUS, TagEffect.PENALTY) and points <= 0:
        return (
            Violation(
                "points-required",
                "points",
                "Bonus e penalità hanno bisogno di punti maggiori di zero.",
            ),
        )
    return ()
