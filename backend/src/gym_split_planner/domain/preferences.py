"""Preferenze della scheda (modello dati, § 4.7): lettura e normalizzazione.

Il JSON delle preferenze è salvato nella scheda. La **lettura** è tollerante: un
valore che non si riconosce si ignora e vale il catalogo o il valore predefinito,
invece di rendere illeggibile la scheda. La **normalizzazione**, al salvataggio, è
stretta: toglie ciò che coincide con il catalogo e i codici che non esistono più,
poi controlla i valori effettivi (regole 1-5 del § 4.7).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from gym_split_planner.domain.catalog_rules import Violation, check_band, check_tag
from gym_split_planner.domain.enums import Priority, TagEffect
from gym_split_planner.domain.model import (
    MuscleOverride,
    MuscleTarget,
    Overrides,
    TagOverride,
    TagRule,
)
from gym_split_planner.domain.scoring import Preferences

PREFERENCES_VERSION = 2
DEFAULT_MAX_SESSION_MINUTES = 75


@dataclass(frozen=True)
class PlanPreferences:
    """Preferenze lette dalla scheda, con i valori predefiniti dove mancano."""

    equipment_order: tuple[str, ...]
    max_session_minutes: float | None = DEFAULT_MAX_SESSION_MINUTES
    overrides: Overrides = field(default_factory=Overrides)

    @property
    def scoring(self) -> Preferences:
        """La parte che serve al punteggio dei candidati."""
        return Preferences(self.equipment_order, self.overrides)


def default_preferences(equipment: Sequence[str]) -> dict[str, Any]:
    """JSON delle preferenze di una scheda nuova: catalogo e ordine degli attrezzi."""
    return {
        "version": PREFERENCES_VERSION,
        "equipment_order": list(equipment),
        "max_session_minutes": DEFAULT_MAX_SESSION_MINUTES,
        "overrides": {"muscles": {}, "tags": {}},
    }


def plan_preferences(preferences: Mapping[str, Any], equipment: Sequence[str]) -> PlanPreferences:
    """Legge le preferenze salvate; ``equipment`` è l'ordine predefinito degli attrezzi."""
    order = preferences.get("equipment_order")
    equipment_order = tuple(equipment)
    if _is_permutation(order, equipment):
        assert isinstance(order, list)
        equipment_order = tuple(str(e) for e in order)
    if "max_session_minutes" in preferences and preferences["max_session_minutes"] is None:
        max_minutes: float | None = None
    else:
        max_minutes = _number(preferences.get("max_session_minutes"))
        if max_minutes is None:
            max_minutes = DEFAULT_MAX_SESSION_MINUTES
    return PlanPreferences(
        equipment_order=equipment_order,
        max_session_minutes=max_minutes,
        overrides=overrides_from_preferences(preferences),
    )


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


def normalize_preferences(
    preferences: Mapping[str, Any],
    muscles: Mapping[str, MuscleTarget],
    tags: Mapping[str, TagRule],
    equipment: Sequence[str],
) -> tuple[dict[str, Any], tuple[Violation, ...]]:
    """Preferenze pronte da salvare, e le regole violate dai valori effettivi.

    - L'ordine degli attrezzi deve contenere ogni attrezzo una volta sola.
    - Si tengono solo i campi diversi dal catalogo; un muscolo o un'etichetta senza
      differenze sparisce, così la scheda torna a seguire il catalogo (regola 1).
    - I codici che non esistono più nel catalogo si tolgono (regola 5).
    - Con priorità effettiva "nessun obiettivo" la fascia non si salva.
    - I valori effettivi devono essere validi: fascia per i muscoli con un obiettivo,
      punti positivi per bonus e penalità (regola 4). Il ``field`` della violazione è
      il percorso nel JSON, es. ``overrides.muscles.quads.weekly_max``.
    """
    violations: list[Violation] = []

    order = preferences.get("equipment_order", list(equipment))
    if not _is_permutation(order, equipment):
        violations.append(
            Violation(
                "equipment-order",
                "equipment_order",
                "L'ordine degli attrezzi deve contenere ogni attrezzo una volta sola.",
            )
        )
        order = list(equipment)

    if "max_session_minutes" in preferences:
        max_minutes = preferences["max_session_minutes"]
    else:
        max_minutes = DEFAULT_MAX_SESSION_MINUTES

    overrides = overrides_from_preferences(preferences)
    muscle_entries: dict[str, dict[str, Any]] = {}
    for code, override in overrides.muscles.items():
        target = muscles.get(code)
        if target is None:
            continue
        entry, found = _normalize_muscle(code, target, override)
        violations.extend(found)
        if entry:
            muscle_entries[code] = entry

    tag_entries: dict[str, dict[str, Any]] = {}
    for code, tag_override in overrides.tags.items():
        rule = tags.get(code)
        if rule is None:
            continue
        tag_entry, found = _normalize_tag(code, rule, tag_override)
        violations.extend(found)
        if tag_entry:
            tag_entries[code] = tag_entry

    return (
        {
            "version": PREFERENCES_VERSION,
            "equipment_order": [str(e) for e in order],
            "max_session_minutes": max_minutes,
            "overrides": {"muscles": muscle_entries, "tags": tag_entries},
        },
        tuple(violations),
    )


def _normalize_muscle(
    code: str, target: MuscleTarget, override: MuscleOverride
) -> tuple[dict[str, Any], list[Violation]]:
    entry: dict[str, Any] = {}
    if override.priority is not None and override.priority != target.priority:
        entry["priority"] = override.priority.value
    priority = override.priority or target.priority
    if priority is Priority.NONE:
        return entry, []
    for name, value, catalog in (
        ("weekly_min", override.weekly_min, target.weekly_min),
        ("weekly_max", override.weekly_max, target.weekly_max),
    ):
        if value is not None and value != catalog:
            entry[name] = value
    weekly_min = entry.get("weekly_min", target.weekly_min)
    weekly_max = entry.get("weekly_max", target.weekly_max)
    found = [
        Violation(v.rule, f"overrides.muscles.{code}.{v.field}", v.message)
        for v in check_band(priority, weekly_min, weekly_max)
    ]
    return entry, found


def _normalize_tag(
    code: str, rule: TagRule, override: TagOverride
) -> tuple[dict[str, Any], list[Violation]]:
    entry: dict[str, Any] = {}
    if override.effect is not None and override.effect != rule.effect:
        entry["effect"] = override.effect.value
    effect = override.effect or rule.effect
    uses_points = effect in (TagEffect.BONUS, TagEffect.PENALTY)
    if uses_points and override.points is not None and override.points != rule.points:
        entry["points"] = override.points
    points = entry.get("points", rule.points)
    found = [
        Violation(v.rule, f"overrides.tags.{code}.{v.field}", v.message)
        for v in check_tag(effect, points)
    ]
    return entry, found


def _is_permutation(order: object, equipment: Sequence[str]) -> bool:
    """Vero se ``order`` contiene ogni attrezzo esattamente una volta."""
    return (
        isinstance(order, list)
        and len(order) == len(equipment)
        and sorted(str(e) for e in order) == sorted(equipment)
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
