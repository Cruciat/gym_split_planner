"""Preferenze della scheda (modello dati, § 4.7): lettura delle personalizzazioni.

Il JSON delle preferenze è salvato nella scheda; qui si legge la parte che serve ai
calcoli, le personalizzazioni di muscoli ed etichette. La lettura è tollerante: un
valore che non si riconosce si ignora e vale il catalogo, invece di rendere
illeggibile la scheda. La validazione stretta avviene al salvataggio (API, § 6.6).
"""

from collections.abc import Mapping
from typing import Any

from gym_split_planner.domain.enums import Priority, TagEffect
from gym_split_planner.domain.model import MuscleOverride, Overrides, TagOverride


def overrides_from_preferences(preferences: Mapping[str, Any]) -> Overrides:
    """Personalizzazioni di muscoli ed etichette, per ``code``."""
    raw = preferences.get("overrides")
    if not isinstance(raw, Mapping):
        return Overrides()
    return Overrides(
        muscles={
            code: _muscle(value)
            for code, value in _entries(raw.get("muscles"))
            if isinstance(value, Mapping)
        },
        tags={
            code: _tag(value)
            for code, value in _entries(raw.get("tags"))
            if isinstance(value, Mapping)
        },
    )


def _entries(value: object) -> list[tuple[str, object]]:
    if not isinstance(value, Mapping):
        return []
    return [(str(code), entry) for code, entry in value.items()]


def _number(value: object) -> float | None:
    # bool è un int in Python: un true nel JSON non è un numero di serie.
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    return None


def _enum[E: (Priority, TagEffect)](enum: type[E], value: object) -> E | None:
    return next((member for member in enum if member.value == value), None)


def _muscle(value: Mapping[str, object]) -> MuscleOverride:
    return MuscleOverride(
        priority=_enum(Priority, value.get("priority")),
        weekly_min=_number(value.get("weekly_min")),
        weekly_max=_number(value.get("weekly_max")),
    )


def _tag(value: Mapping[str, object]) -> TagOverride:
    return TagOverride(
        effect=_enum(TagEffect, value.get("effect")),
        points=_number(value.get("points")),
    )
